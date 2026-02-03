from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    DateTime,
    ForeignKey,
    Boolean,
    JSON,
    Float,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


# 🟢 1. 新增：用户表
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)  # 用户名唯一
    hashed_password = Column(String(100), nullable=False)  # 存加密后的密码，不是明文！
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # 建立关系：一个用户有多个会话
    sessions = relationship(
        "ChatSession", back_populates="owner", cascade="all, delete-orphan"
    )

    interview_records = relationship("InterviewRecord", back_populates="user")


# 🟢 2. 修改：会话列表表
class ChatSession(Base):
    __tablename__ = "chat_sessions"

    id = Column(String(64), primary_key=True, index=True)

    # 🔥 新增 user_id 外键
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    title = Column(String(100), default="新对话")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # 关系：多对一 (多个 Session 属于一个 User)
    owner = relationship("User", back_populates="sessions")

    messages = relationship(
        "ChatMessage", back_populates="session", cascade="all, delete-orphan"
    )


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(
        String(64), ForeignKey("chat_sessions.id"), index=True, nullable=False
    )
    role = Column(String(20), nullable=False)
    content = Column(Text, nullable=False)

    # --- 原有字段 (保持不变) ---
    # 存本地/服务器 URL，供前端 <image> 或下载链接使用
    image_url = Column(Text, nullable=True)

    # --- 🟢 新增字段 (请添加这三行) ---
    # 存 Google 的资源 URI，供后端调用 Gemini 模型使用
    file_uri = Column(String(255), nullable=True)

    # 存文件类型 (如 application/pdf, image/png)
    file_mime_type = Column(String(100), nullable=True)

    # 存文件名 (如 "简历.pdf")，用于前端显示文件名
    file_original_name = Column(String(255), nullable=True)
    # --------------------------------

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    session = relationship("ChatSession", back_populates="messages")


class VerificationCode(Base):
    __tablename__ = "verification_codes"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(100), index=True, nullable=False)
    code = Column(String(10), nullable=False)
    is_used = Column(Boolean, default=False)  # 是否已使用
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class InterviewSession(Base):
    __tablename__ = "interview_sessions"

    id = Column(Integer, primary_key=True, index=True)

    # 关联到基础的聊天会话 (一对一关系)
    session_id = Column(
        String(64), ForeignKey("chat_sessions.id"), unique=True, nullable=False
    )

    # 面试配置
    topic = Column(String(50), nullable=False)  # 例如 'Python', 'Frontend'
    difficulty = Column(String(20), nullable=False)  # 例如 '资深/5年'
    status = Column(String(20), default="ongoing")  # 'ongoing', 'completed'

    # 进度控制
    current_round = Column(Integer, default=0)  # 当前第几轮 (0-10)
    max_rounds = Column(Integer, default=10)  # 总轮次

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # 关系：关联回 ChatSession
    chat_session = relationship("ChatSession", backref="interview_state")


# 🟢 4. 新增：面试评估报告表 (InterviewReport)
class InterviewReport(Base):
    __tablename__ = "interview_reports"

    id = Column(Integer, primary_key=True, index=True)

    # 关联到面试会话
    interview_session_id = Column(
        Integer, ForeignKey("interview_sessions.id"), nullable=False
    )

    # 结构化评分数据
    total_score = Column(Integer)  # 总分 (0-100)
    dimensions = Column(JSON)  # 维度分：{"基础": 80, "架构": 60}
    feedback = Column(Text)  # AI 的总结评价
    level_assessment = Column(String(50))  # 评级：P5, P6, P7

    created_at = Column(DateTime(timezone=True), server_default=func.now())


class Question(Base):
    __tablename__ = "questions"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), index=True)  # 题目标题
    category = Column(String(50), index=True)  # 分类：Python, Redis...
    difficulty = Column(String(20))  # 难度：简单, 中等, 困难
    content = Column(Text)  # 详细解析/答案
    freq = Column(Integer, default=1)  # 考频
    is_mastered = Column(
        Boolean, default=False
    )  # 是否掌握 (简单起见存这里，实际应在关联表)
    created_at = Column(DateTime, default=func.now())


class UserQuestionStatus(Base):
    __tablename__ = "user_question_status"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False)  # 用户ID
    question_id = Column(Integer, nullable=False)  # 题目ID
    is_mastered = Column(Boolean, default=False)  # 是否掌握


class InterviewRecord(Base):
    __tablename__ = "interview_records"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # 🔥🔥🔥 新增：关联 session_id，方便历史回溯 🔥🔥🔥
    session_id = Column(String(64), index=True, nullable=True)

    question_id = Column(Integer, nullable=True)
    score = Column(Integer, default=0)
    summary = Column(Text)
    strengths = Column(JSON)
    suggestions = Column(JSON)
    duration_seconds = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="interview_records")
