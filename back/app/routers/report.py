from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.database import get_db
from app import model, schemas  # 注意：这里引用的是 app.utils.model
from app.services import ai_service

router = APIRouter(prefix="/api/report", tags=["report"])


# 1. 结束面试 -> 生成报告 -> 存入数据库 -> 🔥标记会话结束
@router.post("/generate", response_model=schemas.ReportResponse)
async def generate_report(
    request: schemas.ReportRequest, db: Session = Depends(get_db)
):
    # 1. 调用 AI 生成评分
    ai_result = await ai_service.generate_interview_report(request.chat_history)

    # 2. 保存记录到数据库
    new_record = model.InterviewRecord(
        user_id=request.user_id,
        session_id=request.session_id,  # 🔥🔥🔥 新增：保存 session_id，方便以后查
        question_id=request.question_id,
        score=ai_result.get("score", 0),
        summary=ai_result.get("comment", ""),
        strengths=ai_result.get("strengths", []),
        suggestions=ai_result.get("suggestions", []),
    )
    db.add(new_record)

    # 3. 🔥🔥🔥 新增：将面试会话标记为 "completed" (已完成)
    # 这样用户下次点进来，前端就知道直接显示“报告”按钮，而不是“交卷”
    if request.session_id:
        interview_session = (
            db.query(model.InterviewSession)
            .filter(model.InterviewSession.session_id == request.session_id)
            .first()
        )
        if interview_session:
            interview_session.status = "completed"

    db.commit()
    db.refresh(new_record)

    return schemas.ReportResponse(
        score=new_record.score,
        comment=new_record.summary,
        strengths=new_record.strengths,
        suggestions=new_record.suggestions,
    )


# 2. 首页看板：获取用户的统计数据 (保持不变)
@router.get("/stats/{user_id}", response_model=schemas.UserStatsResponse)
def get_user_stats(user_id: int, db: Session = Depends(get_db)):
    # 查询总次数
    count = (
        db.query(model.InterviewRecord)
        .filter(model.InterviewRecord.user_id == user_id)
        .count()
    )

    # 查询平均分
    avg_score = (
        db.query(func.avg(model.InterviewRecord.score))
        .filter(model.InterviewRecord.user_id == user_id)
        .scalar()
    )

    return schemas.UserStatsResponse(
        interview_count=count, average_score=int(avg_score) if avg_score else 0
    )
