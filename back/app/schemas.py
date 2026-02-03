# app/schemas.py
from pydantic import BaseModel, EmailStr, field_validator
import re
from typing import Optional, Any, List


# ================= 1. 验证码相关 =================
class EmailSchema(BaseModel):
    email: EmailStr


# ================= 2. 登录专用 =================
# 登录只需要用户名和密码，不需要邮箱和验证码
class UserLogin(BaseModel):
    username: str
    password: str


# ================= 3. 注册专用 =================
# 注册需要：用户名 + 密码 + 邮箱 + 验证码
class UserCreate(BaseModel):
    username: str
    password: str
    email: EmailStr
    code: str  # 必填：验证码

    # 密码强度校验
    @field_validator("password")
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError("密码长度不能少于 8 位")
        if not re.search(r"\d", v):
            raise ValueError("密码必须包含至少一个数字")
        if not re.search(r"[a-z]", v):
            raise ValueError("密码必须包含至少一个小写字母")
        if not re.search(r"[A-Z]", v):
            raise ValueError("密码必须包含至少一个大写字母")
        return v


# ================= 4. 其他模型 (保持不变) =================
class UserOut(BaseModel):
    id: int
    username: str

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str
    user_id: int
    username: str


class ChatRequest(BaseModel):
    session_id: str
    content: str
    use_deep_thinking: bool = False
    use_search: bool = False
    memory_limit: int = 10


class SessionCreate(BaseModel):
    title: str = "新对话"


class SessionUpdate(BaseModel):
    title: str


class ReportRequest(BaseModel):
    user_id: int  # 实际生产中应从 Token 获取，这里方便调试
    question_id: Optional[int] = None
    chat_history: List[dict]  # 格式: [{"role": "user", "content": "..."}, ...]
    session_id: str


# 2. 返回给前端的报告数据
class ReportResponse(BaseModel):
    score: int
    comment: str
    strengths: List[str]
    suggestions: List[str]


# 3. 首页看板数据
class UserStatsResponse(BaseModel):
    interview_count: int
    average_score: int
