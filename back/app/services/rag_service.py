# app/services/rag_service.py

import os
import chromadb

# 🟢 1. 引入 Chroma 自带的 embedding 工具
from chromadb.utils import embedding_functions
from langchain_text_splitters import RecursiveCharacterTextSplitter
from dotenv import load_dotenv
import pypdf

load_dotenv()

# 初始化 ChromaDB
chroma_client = chromadb.PersistentClient(path="./chroma_db")

# 🔥🔥🔥 保持你选择的 BAAI 本地模型不变 🔥🔥🔥
MODEL_NAME = "BAAI/bge-small-zh-v1.5"

# 设置 HuggingFace 镜像 (防下载卡顿)
os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"

local_embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
    model_name=MODEL_NAME
)

# 获取/创建集合
collection = chroma_client.get_or_create_collection(
    name="interview_knowledge_base_local",
    embedding_function=local_embedding_fn,
)


def extract_text_from_file(file_path: str) -> str:
    ext = os.path.splitext(file_path)[1].lower()
    text_content = ""
    try:
        if ext == ".pdf":
            reader = pypdf.PdfReader(file_path)
            for page in reader.pages:
                text_content += page.extract_text() + "\n"
        else:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                text_content = f.read()
        return text_content
    except Exception as e:
        print(f"❌ 解析失败 {file_path}: {e}")
        return ""


def add_document_to_kb(file_path: str, source_name: str):
    text = extract_text_from_file(file_path)
    if not text or len(text) < 10:
        return 0

    splitter = RecursiveCharacterTextSplitter(chunk_size=600, chunk_overlap=100)
    chunks = splitter.split_text(text)

    if not chunks:
        return 0

    ids = [f"{source_name}_{i}" for i in range(len(chunks))]
    metadatas = [{"source": source_name} for _ in chunks]

    collection.add(documents=chunks, ids=ids, metadatas=metadatas)
    print(f"✅ 成功导入: {source_name} (共 {len(chunks)} 个切片)")
    return len(chunks)


def list_documents_in_kb():
    try:
        all_data = collection.get(include=["metadatas"])
        file_stats = {}
        for meta in all_data["metadatas"]:
            source_name = meta.get("source", "Unknown")
            file_stats[source_name] = file_stats.get(source_name, 0) + 1
        result = []
        for name, count in file_stats.items():
            result.append({"filename": name, "chunks_count": count})
        return result
    except Exception as e:
        print(f"查询列表失败: {e}")
        return []


# 🔥🔥🔥 核心修复：增加阈值过滤 🔥🔥🔥
def search_knowledge(query: str, top_k: int = 3):
    try:
        # ChromaDB 默认返回 distances (距离)，越小越相似
        results = collection.query(query_texts=[query], n_results=top_k)

        valid_documents = []
        if results["distances"]:
            for i, dist in enumerate(results["distances"][0]):
                # 🟢 阈值控制：0.6 是一个经验值
                # 如果距离大于 0.6，说明内容风马牛不相及（比如搜Python出了Java），直接丢弃
                if dist < 0.6:
                    valid_documents.append(results["documents"][0][i])
                else:
                    # 可以在这里打印日志看看被过滤掉的内容
                    # print(f"过滤低相关文档 (dist={dist}): {results['documents'][0][i][:10]}...")
                    pass

        return valid_documents
    except Exception as e:
        print(f"RAG Search Error: {e}")
        return []
