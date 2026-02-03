# app/routers/question_bank.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

# 🟢 新增导入 or_ 用于复杂查询
from sqlalchemy import or_
from typing import List, Optional
from pydantic import BaseModel

from app.database import get_db
from app.model import Question, User, UserQuestionStatus

# 适配你的目录结构，确保能导入 get_current_user
try:
    from app.routers.auth import get_current_user
except ImportError:
    from app.routers.auth import get_current_user

router = APIRouter(prefix="/api/questions", tags=["QuestionBank"])


# --- Pydantic 模型 ---
class QuestionOut(BaseModel):
    id: int
    title: str
    category: str
    difficulty: str
    content: str
    freq: int
    is_mastered: bool

    class Config:
        from_attributes = True  # Pydantic v2 写法，v1用 orm_mode = True


# --- 路由逻辑 ---


@router.get("/list", response_model=List[QuestionOut])
def get_questions(
    category: Optional[str] = None,
    difficulty: Optional[str] = None,
    keyword: Optional[str] = None,
    status: str = "all",
    # 🟢 新增分页参数
    page: int = 1,
    page_size: int = 20,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    获取题库列表，支持按掌握状态筛选
    """
    # 🟢 1. 构建联合查询
    # 我们不仅查 Question，还顺带查出 UserQuestionStatus.is_mastered
    # outerjoin: 即使没有做过这道题（UserQuestionStatus 为空），题目也会被查出来
    query = db.query(Question, UserQuestionStatus.is_mastered).outerjoin(
        UserQuestionStatus,
        (Question.id == UserQuestionStatus.question_id)
        & (UserQuestionStatus.user_id == current_user.id),
    )

    # 🟢 2. 应用基础筛选
    if category and category != "all":
        query = query.filter(Question.category.ilike(f"%{category}%"))

    if difficulty and difficulty != "全部":
        query = query.filter(Question.difficulty == difficulty)

    if keyword:
        query = query.filter(Question.title.ilike(f"%{keyword}%"))

    # 🟢 3. 应用“掌握状态”筛选 (核心逻辑)
    if status == "mastered":
        # 只看已掌握
        query = query.filter(UserQuestionStatus.is_mastered == True)
    elif status == "unmastered":
        # 未掌握 = 记录显式为False OR 根本没有记录(None)
        query = query.filter(
            or_(
                UserQuestionStatus.is_mastered == False,
                UserQuestionStatus.is_mastered == None,
            )
        )

    # 4. 排序与分页
    # 既然已经 Filter 过了，现在 limit(50) 拿到的就是真正符合条件的数据
    offset = (page - 1) * page_size

    # 获取数据
    offset = (page - 1) * page_size

    # 获取数据
    results = query.order_by(Question.freq.desc()).offset(offset).limit(page_size).all()
    # 5. 组装返回数据
    # 因为查询返回的是 tuple: (Question对象, is_mastered布尔值)
    response_data = []
    for q, is_mastered_val in results:
        # 构造 Pydantic 需要的字典
        q_dict = {
            "id": q.id,
            "title": q.title,
            "category": q.category,
            "difficulty": q.difficulty,
            "content": q.content,
            "freq": q.freq,
            # 处理 None 的情况，如果没有记录，默认为 False
            "is_mastered": True if is_mastered_val else False,
        }
        response_data.append(q_dict)

    return response_data


@router.post("/toggle_master")
def toggle_master(
    question_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # 查找记录
    status_record = (
        db.query(UserQuestionStatus)
        .filter(
            UserQuestionStatus.user_id == current_user.id,
            UserQuestionStatus.question_id == question_id,
        )
        .first()
    )

    if status_record:
        # 取反
        status_record.is_mastered = not status_record.is_mastered
    else:
        # 创建新记录
        new_status = UserQuestionStatus(
            user_id=current_user.id, question_id=question_id, is_mastered=True
        )
        db.add(new_status)

    db.commit()
    return {"msg": "success"}
