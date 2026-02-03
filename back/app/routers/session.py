import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

# 🟢 导入 Auth 依赖和 Model
from app.database import get_db
from app import model, schemas
from app.routers.auth import get_current_user  # 假设 auth.py 在 routers 下

router = APIRouter(prefix="/sessions", tags=["Sessions"])


# 1. 获取会话列表 (已加权)
@router.get("/list")
def get_session_list(
    db: Session = Depends(get_db),
    current_user: model.User = Depends(get_current_user),  # 🟢 必须登录
):
    """
    获取当前用户的会话列表
    """
    sessions = (
        db.query(model.ChatSession)
        .filter(model.ChatSession.user_id == current_user.id)  # 🔒 只查自己的
        .order_by(model.ChatSession.updated_at.desc())
        .all()
    )

    result = []
    for s in sessions:
        result.append(
            {
                "id": s.id,
                "title": s.title,
                "updated_at": (
                    s.updated_at.strftime("%Y-%m-%d %H:%M") if s.updated_at else ""
                ),
            }
        )

    return {"code": 200, "data": result}


# 2. 创建新会话 (已加权)
@router.post("/create")
def create_session(
    request: schemas.SessionCreate,
    db: Session = Depends(get_db),
    current_user: model.User = Depends(get_current_user),  # 🟢 必须登录
):
    new_id = f"sess_{uuid.uuid4().hex}"

    new_session = model.ChatSession(
        id=new_id, title=request.title, user_id=current_user.id  # 🔒 绑定当前用户ID
    )

    db.add(new_session)
    db.commit()
    db.refresh(new_session)

    return {
        "code": 200,
        "message": "创建成功",
        "data": {"session_id": new_session.id, "title": new_session.title},
    }


# 3. 修改会话标题 (已加权)
@router.patch("/{session_id}")
def update_session_title(
    session_id: str,
    request: schemas.SessionUpdate,
    db: Session = Depends(get_db),
    current_user: model.User = Depends(get_current_user),
):
    # 🔒 查找时同时校验 ID 和 UserID
    session = (
        db.query(model.ChatSession)
        .filter(
            model.ChatSession.id == session_id,
            model.ChatSession.user_id == current_user.id,
        )
        .first()
    )

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    session.title = request.title
    db.commit()

    return {"code": 200, "message": "标题已更新", "data": {"title": session.title}}


# 4. 删除会话 (已加权)
@router.delete("/{session_id}")
def delete_session(
    session_id: str,
    db: Session = Depends(get_db),
    current_user: model.User = Depends(get_current_user),
):
    # 🔒 只能删除自己的会话
    session = (
        db.query(model.ChatSession)
        .filter(
            model.ChatSession.id == session_id,
            model.ChatSession.user_id == current_user.id,
        )
        .first()
    )

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    db.delete(session)
    db.commit()

    return {"code": 200, "message": "删除成功"}
