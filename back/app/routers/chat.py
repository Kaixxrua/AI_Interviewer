# app/routers/chat.py

import shutil
import os
import uuid
import json
from typing import Optional
from fastapi import (
    APIRouter,
    Depends,
    UploadFile,
    File,
    Form,
    Query,
    Request,
    HTTPException,
)
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.database import get_db
from app.model import ChatSession, ChatMessage, User, InterviewSession
from app import model
from app.services.ai_service import (
    stream_ai_response,
    save_message,
    upload_file_to_gemini,
)
from app.routers.auth import get_current_user

router = APIRouter()


class DeleteMessageRequest(BaseModel):
    session_id: str
    message_id: int
    delete_after: bool = False


class StartInterviewRequest(BaseModel):
    topic: str
    difficulty: str


def verify_session_ownership(db: Session, session_id: str, user_id: int):
    session = (
        db.query(ChatSession)
        .filter(ChatSession.id == session_id, ChatSession.user_id == user_id)
        .first()
    )
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session


@router.post("/chat/interview/start")
def start_interview(
    req: StartInterviewRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    new_session_id = str(uuid.uuid4())
    chat_session = ChatSession(
        id=new_session_id, user_id=current_user.id, title=f"{req.topic} 模拟面试"
    )
    db.add(chat_session)
    interview_state = InterviewSession(
        session_id=new_session_id,
        topic=req.topic,
        difficulty=req.difficulty,
        current_round=0,
        max_rounds=10,
        status="ongoing",
    )
    db.add(interview_state)
    db.commit()
    return {
        "code": 200,
        "msg": "面试已创建",
        "data": {"session_id": new_session_id, "topic": req.topic},
    }


@router.post("/chat")
async def chat_endpoint(
    request: Request,
    session_id: str = Form(...),
    content: str = Form(...),
    use_deep_thinking: bool = Form(False),
    use_search: bool = Form(False),
    memory_limit: int = Form(10),
    file: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    verify_session_ownership(db, session_id, current_user.id)

    interview_context = None
    interview_state = (
        db.query(InterviewSession)
        .filter(InterviewSession.session_id == session_id)
        .first()
    )
    if interview_state and interview_state.status == "ongoing":
        if interview_state.current_round < interview_state.max_rounds:
            interview_state.current_round += 1
            db.commit()
            db.refresh(interview_state)
        interview_context = {
            "topic": interview_state.topic,
            "difficulty": interview_state.difficulty,
            "current_round": interview_state.current_round,
            "max_rounds": interview_state.max_rounds,
        }

    local_file_url, gemini_file_uri, file_mime, file_name = None, None, None, None
    if file:
        file_name = file.filename or "unknown"
        file_mime = file.content_type or "application/octet-stream"
        file_ext = file_name.split(".")[-1] if "." in file_name else "bin"
        local_filename = f"{uuid.uuid4()}.{file_ext}"
        os.makedirs("uploads", exist_ok=True)
        local_file_path = f"uploads/{local_filename}"
        with open(local_file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        base_url = str(request.base_url).rstrip("/")
        local_file_url = f"{base_url}/uploads/{local_filename}"
        try:
            uploaded = upload_file_to_gemini(local_file_path, mime_type=file_mime)
            if uploaded:
                gemini_file_uri = uploaded.uri
        except Exception:
            pass

    user_msg_id = save_message(
        db,
        session_id,
        "user",
        content,
        image_url=local_file_url,
        file_uri=gemini_file_uri,
        file_mime_type=file_mime,
        file_original_name=file_name,
    )

    def event_generator():
        yield f"data: {json.dumps({'type': 'meta_user', 'id': user_msg_id})}\n\n"
        full_ai_text = ""
        stream = stream_ai_response(
            db=db,
            session_id=session_id,
            user_message=content,
            use_deep_thinking=use_deep_thinking,
            use_search=use_search,
            memory_limit=memory_limit,
            pre_uploaded_file_uri=gemini_file_uri,
            file_mime_type=file_mime,
            file_original_name=file_name,
            use_rag_bank=True,
            interview_context=interview_context,
        )
        for chunk in stream:
            if chunk:
                full_ai_text += chunk
                yield f"data: {json.dumps({'text': chunk}, ensure_ascii=False)}\n\n"

        if full_ai_text:
            ai_msg_id = save_message(db, session_id, "model", full_ai_text)
            yield f"data: {json.dumps({'type': 'meta_ai', 'id': ai_msg_id})}\n\n"
            if (
                interview_context
                and interview_context["current_round"]
                >= interview_context["max_rounds"]
            ):
                yield f"data: {json.dumps({'type': 'interview_end'})}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@router.get("/chat/history")
def get_chat_history(
    session_id: str = Query(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    verify_session_ownership(db, session_id, current_user.id)
    messages = (
        db.query(ChatMessage)
        .filter(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.created_at.asc())
        .all()
    )

    interview_state = (
        db.query(model.InterviewSession)
        .filter(model.InterviewSession.session_id == session_id)
        .first()
    )

    interview_meta = None
    report_data = None  # 🔥 新增：用于存储报告数据

    if interview_state:
        interview_meta = {
            "is_interview": True,
            "current_round": interview_state.current_round,
            "max_rounds": interview_state.max_rounds,
            "topic": interview_state.topic,
            "difficulty": interview_state.difficulty,
            "status": interview_state.status,  # 🔥 确保传回 status
        }

        # 🔥🔥🔥 核心修改：如果已完成，查出报告一起返回 🔥🔥🔥
        if interview_state.status == "completed":
            record = (
                db.query(model.InterviewRecord)
                .filter(model.InterviewRecord.session_id == session_id)
                .order_by(model.InterviewRecord.created_at.desc())
                .first()
            )
            if record:
                report_data = {
                    "score": record.score,
                    "comment": record.summary,
                    "strengths": record.strengths,
                    "suggestions": record.suggestions,
                }

    result = []
    for msg in messages:
        role = "assistant" if msg.role == "model" else "user"
        item = {
            "id": msg.id,
            "role": role,
            "content": msg.content,
            "image": msg.image_url,
        }
        if msg.file_mime_type:
            item["file_meta"] = {
                "name": msg.file_original_name,
                "mime": msg.file_mime_type,
                "is_pdf": "pdf" in msg.file_mime_type.lower(),
            }
        result.append(item)

    return {
        "code": 200,
        "data": result,
        "interview_meta": interview_meta,
        "report_data": report_data,  # 👈 将报告数据传给前端
    }


@router.post("/chat/message/delete")
def delete_message(
    req: DeleteMessageRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    verify_session_ownership(db, req.session_id, current_user.id)
    if req.delete_after:
        db.query(ChatMessage).filter(
            ChatMessage.session_id == req.session_id, ChatMessage.id >= req.message_id
        ).delete(synchronize_session=False)
    else:
        db.query(ChatMessage).filter(
            ChatMessage.id == req.message_id, ChatMessage.session_id == req.session_id
        ).delete()
    db.commit()
    return {"status": "success"}
