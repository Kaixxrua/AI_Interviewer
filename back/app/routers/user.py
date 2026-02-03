# app/routers/user.py (建议新建这个文件)

from fastapi import APIRouter, UploadFile, File, Depends, Form
from fastapi.staticfiles import StaticFiles
import shutil
import os
import uuid
from app.routers.auth import get_current_user
from app.model import User

router = APIRouter(prefix="/api/user", tags=["user"])

# 确保 uploads 目录存在
os.makedirs("uploads/avatars", exist_ok=True)


@router.post("/upload-avatar")
async def upload_avatar(
    file: UploadFile = File(...),
    user_id: int = Form(...),  # 也可以直接用 current_user 获取
    current_user: User = Depends(get_current_user),
):
    # 1. 生成唯一文件名
    file_ext = file.filename.split(".")[-1]
    filename = f"avatar_{user_id}_{uuid.uuid4().hex[:8]}.{file_ext}"
    file_path = f"uploads/avatars/{filename}"

    # 2. 保存文件到本地
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # 3. 生成可访问的 URL (假设你的服务器运行在 8000 端口)
    # 注意：需要在 main.py 里 mount StaticFiles
    url = f"http://192.168.2.32:8000/uploads/avatars/{filename}"

    # 4. (可选) 这里可以更新数据库中 User 表的 avatar 字段
    # current_user.avatar = url
    # db.commit()

    return {"status": "success", "url": url}
