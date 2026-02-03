from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os

# 1. 导入路由模块
from app.routers import (
    chat,
    session,
    auth,
    admin,
    question_bank,
    report,
    user,
)  # 🟢 确保导入了 question_bank
from app.database import engine, Base

# 重新建表 (如果表不存在的话)
Base.metadata.create_all(bind=engine)

app = FastAPI()

os.makedirs("uploads", exist_ok=True)
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 2. 注册路由
app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(chat.router, prefix="/api", tags=["chat"])
app.include_router(session.router, prefix="/api", tags=["session"])
app.include_router(admin.router, prefix="/api/admin", tags=["admin"])

# 🔥🔥🔥 注册题库路由 (注意：question_bank.py 里已经定义了 prefix="/api/questions")
app.include_router(question_bank.router)
app.include_router(report.router)
app.include_router(user.router)

# 确保静态文件挂载涵盖了头像目录
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")


@app.get("/")
def read_root():
    return {"Hello": "AI Interviewer with Auth"}
