# app/routers/admin.py

from fastapi import APIRouter, UploadFile, File, HTTPException
import shutil
import os
import uuid

# 确保导入路径正确
from app.services.rag_service import add_document_to_kb, list_documents_in_kb

router = APIRouter()


@router.post("/rag/upload")
async def upload_knowledge_file(file: UploadFile = File(...)):
    """
    管理员接口：上传 PDF/Markdown 到 RAG 知识库
    """
    # 1. 存临时文件
    file_ext = file.filename.split(".")[-1]
    temp_filename = f"temp_rag_{uuid.uuid4()}.{file_ext}"

    with open(temp_filename, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    try:
        # 2. 调用 RAG 服务入库
        # source_name 用原始文件名，方便以后知道是哪本书里的
        count = add_document_to_kb(temp_filename, file.filename)

        return {
            "code": 200,
            "message": "Upload success",
            "data": {"filename": file.filename, "chunks_added": count},
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        # 3. 清理临时文件
        if os.path.exists(temp_filename):
            os.remove(temp_filename)


@router.get("/rag/list")
async def get_knowledge_list():
    """
    查看当前 RAG 知识库里有哪些文件
    """
    try:
        documents = list_documents_in_kb()
        return {
            "code": 200,
            "message": "success",
            "data": documents,
            "total_files": len(documents),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
