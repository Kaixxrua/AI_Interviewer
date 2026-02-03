import sys
import os
import json
import time

# 将父目录加入路径，以便能导入 app 模块
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import SessionLocal, engine
# 注意：请确认你的模型文件是 model.py 还是 models.py，根据之前的报错应该是 models
from app.model import Base, Question 
from app.services.ai_service import get_llm_response

# 尝试导入 pypdf 以支持 PDF 文件
try:
    from pypdf import PdfReader
except ImportError:
    PdfReader = None

# 确保表存在
Base.metadata.create_all(bind=engine)

def generate_questions_from_text(text_chunk):
    """
    让 AI 从文本中提取结构化题目
    """
    prompt = f"""
    你是专业的面试题整理专家。请阅读下面的技术文档片段，提取其中包含的面试知识点。
    
    【任务要求】
    1. 提取出 1-3 个独立的面试题。
    2. 为每个题目生成：
       - title: 简短的标题（20字以内）。
       - content: 简要的答案或解析（100字以内）。
       - difficulty: 判断难度，只能是 "简单"、"中等"、"困难" 之一。
       - category: 只能从 ["Python", "前端", "Redis", "MySQL", "算法", "高并发", "计算机网络", "操作系统", "HR行为面"] 中选一个最匹配的。
    3. 输出必须是纯 JSON 数组格式，不要包含 Markdown 格式（如 ```json）。

    【文档片段】：
    {text_chunk[:3000]}
    """

    try:
        # 调用你的 LLM 服务
        response = get_llm_response(messages=[{"role": "user", "content": prompt}])
        # 清理可能的 markdown 符号
        cleaned_response = response.replace("```json", "").replace("```", "").strip()
        return json.loads(cleaned_response)
    except Exception as e:
        print(f"   ❌ AI 解析失败: {e}")
        return []

def save_to_db(questions_data):
    db = SessionLocal()
    count = 0
    for q in questions_data:
        # 查重
        exists = db.query(Question).filter(Question.title == q["title"]).first()
        if not exists:
            new_q = Question(
                title=q.get("title", "未知标题"),
                content=q.get("content", "暂无解析"),
                difficulty=q.get("difficulty", "中等"),
                category=q.get("category", "综合"),
                freq=100,
                is_mastered=False,
            )
            db.add(new_q)
            count += 1
    db.commit()
    db.close()
    return count

def process_single_file(file_path):
    """
    处理单个文件的读取和切片逻辑
    """
    text = ""
    filename = os.path.basename(file_path)

    # 1. 读取内容
    if filename.endswith(".txt") or filename.endswith(".md"):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                text = f.read()
        except Exception as e:
            print(f"   ⚠️ 读取文本失败: {filename}, {e}")
            return

    elif filename.endswith(".pdf") and PdfReader:
        try:
            reader = PdfReader(file_path)
            for page in reader.pages:
                text += page.extract_text() or ""
        except Exception as e:
            print(f"   ⚠️ 读取PDF失败: {filename}, {e}")
            return
    else:
        return # 跳过不支持的文件类型

    if not text.strip():
        return

    print(f"📄 正在处理: {file_path}")

    # 2. 切片并调用 AI
    chunk_size = 2000
    total_len = len(text)
    
    # 如果文本太短，至少跑一次
    if total_len < chunk_size:
        chunks = [text]
    else:
        chunks = [text[i : i + chunk_size] for i in range(0, total_len, chunk_size)]

    for idx, chunk in enumerate(chunks):
        print(f"   🤖 请求 AI 提取中... (片段 {idx + 1}/{len(chunks)})")
        
        questions = generate_questions_from_text(chunk)

        if questions:
            added = save_to_db(questions)
            print(f"      ✅ 入库 {added} 题")
        
        # 避免并发太快触发 LLM 限流
        time.sleep(1.5)

def main():
    # 指定根目录（请根据你的实际情况修改路径）
    # 建议使用绝对路径，或者相对于脚本的准确路径
    base_dir = os.path.dirname(os.path.abspath(__file__))
    source_dir = os.path.join(base_dir, "../rag_source") 

    if not os.path.exists(source_dir):
        print(f"❌ 错误: 目录不存在 - {source_dir}")
        return

    print(f"🚀 开始递归遍历目录: {source_dir}")

    # 🔥🔥🔥 核心修改：使用 os.walk 递归遍历 🔥🔥🔥
    for root, dirs, files in os.walk(source_dir):
        for filename in files:
            # 组合完整路径
            file_path = os.path.join(root, filename)
            
            # 调用处理函数
            process_single_file(file_path)

    print("🎉 全部处理完成！")

if __name__ == "__main__":
    main()