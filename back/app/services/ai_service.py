# app/services/ai_service.py

import os
import json
import re
import datetime
import random  #
from typing import Iterator, Optional, Dict, Any

from google import genai
from google.genai import types
from dotenv import load_dotenv
from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.model import ChatMessage

# 尝试导入 RAG 服务
try:
    from app.services.rag_service import search_knowledge
except ImportError:
    print("⚠️ 警告：未找到 app.services.rag_service，RAG 功能将不可用。")

    def search_knowledge(*args, **kwargs):
        return []


TOPIC_VARIATIONS = {
    "Python": [
        "深拷贝与浅拷贝 (Deep vs Shallow Copy)",
        "装饰器 (Decorators) 的原理与应用",
        "生成器 (Generators) 与迭代器 (Iterators)",
        "Python 的内存管理与垃圾回收机制",
        "可变对象与不可变对象 (Mutable vs Immutable)",
        "字典 (Dict) 的底层实现原理",
        "GIL (全局解释器锁) 对多线程的影响",
        "闭包 (Closure) 与作用域",
        "异常处理机制 (try-except-else-finally)",
        "魔法方法 (Magic Methods) 如 __init__, __new__, __call__",
    ],
    "Frontend": [  # 前端
        "Vue/React 的生命周期",
        "浏览器渲染原理与重绘重排",
        "JS 原型链与继承",
        "ES6 新特性 (Promise, Async/Await)",
        "跨域问题的解决方案",
        "前端性能优化手段",
        "CSS 盒模型与 BFC",
        "Vue 响应式原理 (Object.defineProperty vs Proxy)",
    ],
    # ... 你可以继续扩展其他分类
}

# 如果没有匹配到，就用这个通用的
GENERIC_VARIATIONS = [
    "该技术栈的底层原理",
    "实际开发中容易踩的坑",
    "性能优化的最佳实践",
    "与同类技术的对比优势",
    "核心架构设计思想",
]
load_dotenv()

# 配置代理
os.environ["HTTP_PROXY"] = "http://127.0.0.1:7895"
os.environ["HTTPS_PROXY"] = "http://127.0.0.1:7895"

api_key = os.getenv("API_KEY")
if not api_key:
    print("❌ 未找到 API_KEY")

try:
    client = genai.Client(api_key=api_key)
except Exception as e:
    client = None
    print(f"❌ Gemini Client 初始化失败: {e}")


def get_system_prompt(use_deep_thinking: bool = False, interview_context: dict = None):
    current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    base_prompt = f"当前时间：{current_time}\n"

    if interview_context:
        topic = interview_context.get("topic", "通用技术")  # 例如 "Python开发"
        difficulty = interview_context.get(
            "difficulty", "中级"
        )  # 例如 "[校招/实习] - 语法基础"
        current_round = interview_context.get("current_round", 1)
        max_rounds = interview_context.get("max_rounds", 10)

        # 🔥🔥🔥 核心修改：第一轮强制随机选题 🔥🔥🔥
        random_instruction = ""
        if current_round == 1:
            # 1. 简单的关键词匹配，确定技术栈
            key = (
                "Python"
                if "Python" in topic or "Python" in difficulty
                else "Frontend" if "前端" in topic or "Vue" in topic else None
            )

            # 2. 随机抽取一个侧重点
            if key and key in TOPIC_VARIATIONS:
                focus_point = random.choice(TOPIC_VARIATIONS[key])
            else:
                focus_point = random.choice(GENERIC_VARIATIONS)

            # 3. 构造强制指令
            random_instruction = f"""
            【特别指令】：这是面试的第一题。
            为了避免重复，请你**必须**忽略“列表与元组的区别”这种老套问题。
            请重点考察：【{focus_point}】。
            请结合候选人的级别（{difficulty}）设计一个具体的问题。
            """

        base_prompt += f"""
你现在是一位资深的【{topic}】面试官，正在面试一位【{difficulty}】水平的候选人。
当前面试进度：第 {current_round} / {max_rounds} 轮。

【你的行为准则】：
1. 严禁一次性问多个问题，每次只问一个。
2. 如果是第 1 轮，请直接开始提问，不要寒暄。
{random_instruction} 
3. 如果用户回答了上一个问题，请简短点评，然后紧接着问下一个问题。
4. 保持专业，问题要具体，不要太泛。
"""
    else:
        base_prompt += "你是一个专业的 AI 面试官和技术助手。\n"

    if use_deep_thinking:
        base_prompt += """
\n【格式强制指令】
你现在处于【深度思考模式】。
请务必将你的思考过程包裹在 <think> 和 </think> 标签中。
先输出 <think>...思考内容...</think>，再输出最终回答。
"""
    return base_prompt


def upload_file_to_gemini(file_path: str, mime_type: str = None):
    if not client:
        return None
    try:
        uploaded_file = client.files.upload(
            file=file_path, config={"mime_type": mime_type} if mime_type else None
        )
        return uploaded_file
    except Exception:
        return None


def save_message(
    db: Session,
    session_id: str,
    role: str,
    content: str,
    image_url: str = None,
    file_uri: str = None,
    file_mime_type: str = None,
    file_original_name: str = None,
):
    new_msg = ChatMessage(
        session_id=session_id,
        role=role,
        content=content,
        image_url=image_url,
        file_uri=file_uri,
        file_mime_type=file_mime_type,
        file_original_name=file_original_name,
    )
    db.add(new_msg)
    db.commit()
    db.refresh(new_msg)
    return new_msg.id


def get_chat_history(db: Session, session_id: str, limit: int = 20):
    messages = (
        db.query(ChatMessage)
        .filter(ChatMessage.session_id == session_id)
        .order_by(desc(ChatMessage.created_at))
        .limit(limit)
        .all()
    )
    messages.reverse()

    formatted_history = []
    for msg in messages:
        parts = []
        if msg.file_uri and msg.file_mime_type:
            parts.append(
                types.Part.from_uri(file_uri=msg.file_uri, mime_type=msg.file_mime_type)
            )

        clean_content = msg.content
        if "<think>" in clean_content:
            import re

            clean_content = re.sub(
                r"<think>[\s\S]*?</think>", "", clean_content
            ).strip()

        parts.append(types.Part.from_text(text=clean_content))
        formatted_history.append(types.Content(role=msg.role, parts=parts))
    return formatted_history


def stream_ai_response(
    db: Session,
    session_id: str,
    user_message: str,
    use_deep_thinking: bool = False,
    use_search: bool = False,
    memory_limit: int = 10,
    pre_uploaded_file_uri: Optional[str] = None,
    file_mime_type: Optional[str] = None,
    file_original_name: Optional[str] = None,
    use_rag_bank: bool = False,
    interview_context: Optional[dict] = None,
) -> Iterator[str]:

    if not client:
        yield "系统错误：API Key 未配置"
        return

    full_response_text = ""
    gemini_file_uri = pre_uploaded_file_uri

    try:
        # 1. 获取历史
        msg_limit = memory_limit * 2
        history_contents = []
        if msg_limit > 0:
            history_contents = get_chat_history(db, session_id, limit=msg_limit)

        # 2. RAG 检索 (已增加 Prompt 隔离)
        rag_context = ""
        if use_rag_bank:
            try:
                found_docs = search_knowledge(user_message)
                if found_docs:
                    if isinstance(found_docs, list):
                        doc_text = "\n\n".join(found_docs)
                    else:
                        doc_text = str(found_docs)
                    current_topic = (interview_context or {}).get("topic", "通用技术")
                    # 🔥🔥🔥 核心修改：甩锅式 Prompt 🔥🔥🔥
                    rag_context = f"""
【⚠️系统内部参考资料】
(注意：以下内容检索自本地数据库，可能包含与当前面试主题({current_topic})无关的代码。
如果参考资料语言不符，请务必直接忽略，严禁在回复中引用，更不要认为是用户提供的！)

---资料开始---
{doc_text}
---资料结束---
"""
                    print(f"✅ 命中知识库: {len(found_docs)} 条 (已过滤不相关内容)")
            except Exception as e:
                print(f"❌ RAG Error: {e}")

        # 3. 构建 Prompt
        final_prompt = user_message
        if rag_context:
            final_prompt = f"{rag_context}\n用户问题：{user_message}"

        if file_mime_type == "application/pdf":
            final_prompt = f"请阅读附件 PDF：{file_original_name}。\n{final_prompt}"

        current_parts = []
        if gemini_file_uri:
            current_parts.append(
                types.Part.from_uri(file_uri=gemini_file_uri, mime_type=file_mime_type)
            )

        current_parts.append(types.Part.from_text(text=final_prompt))
        final_contents = history_contents + [
            types.Content(role="user", parts=current_parts)
        ]

        tools = []
        if use_search:
            tools.append(types.Tool(google_search=types.GoogleSearch()))

        # 🔥 保持你的模型名称 🔥
        if use_deep_thinking:
            current_model = "gemini-3-pro-preview"
        else:
            current_model = "gemini-3-flash-preview"

        print(f"🚀 Model: {current_model}, DeepThinking: {use_deep_thinking}")

        response_stream = client.models.generate_content_stream(
            model=current_model,
            contents=final_contents,
            config=types.GenerateContentConfig(
                system_instruction=get_system_prompt(
                    use_deep_thinking, interview_context
                ),
                temperature=0.7,
                tools=tools,
                max_output_tokens=8192,
            ),
        )

        for chunk in response_stream:
            text_chunk = chunk.text if hasattr(chunk, "text") else ""
            if text_chunk:
                full_response_text += text_chunk
                yield text_chunk

    except Exception as e:
        print(f"Stream Error: {e}")
        yield f"\n[服务异常: {str(e)}]"


async def generate_interview_report(chat_history: list) -> Dict[str, Any]:
    """
    根据对话历史生成结构化报告 (基于 WHWS 四维模型评分)
    """
    if not client:
        return {
            "score": 0,
            "comment": "AI 服务未连接",
            "strengths": [],
            "suggestions": [],
        }

    # 1. 转换对话历史
    history_text = ""
    for msg in chat_history:
        role = "面试官" if msg.get("role") == "model" else "候选人"
        history_text += f"{role}: {msg.get('content')}\n"

    # 2. 构造深度评估 Prompt (融入你的评分哲学)
    system_prompt = """
    你是一位极度严格且专业的资深技术面试官。面试已结束，请根据【对话历史】生成一份评估报告。
    
    【核心评分标准】：
    技术面试不是“问答考试”，而是“同行切磋”。
    请严格按照 **What-How-Why-Scenarios (WHWS)** 四维模型对候选人的回答进行拆解评分：
    
    1. **What (定义/结论)** - 权重 20%
       - 是否准确给出了定义？
       - 如果只回答了这一层，视为“挤牙膏”式回答，只能给低分。
       
    2. **How (原理/源码)** - 权重 30%
       - 是否展示了深度？(如：底层数据结构、源码机制、线程安全实现等)。
       - 这是区别初级和高级的关键。
       
    3. **Why & Comparison (对比/选型)** - 权重 20%
       - 是否展示了广度？(如：与其他技术方案的横向对比、优缺点权衡)。
       
    4. **Scenarios (场景/实战)** - 权重 30% (杀手锏)
       - 是否结合了实际项目经验？
       - 是否提到了具体的生产问题（如OOM、死锁、性能优化）及解决方案？
    
    【分数段位定义】(请严格执行):
    - **< 60分 (不通过)**: 回答干瘪，仅停留在 What 层面，像挤牙膏一样，一问一答，缺乏深度。
    - **60 - 84分 (通过)**: 基础扎实，能回答出 What 和 How，对原理有一定理解，但缺乏实战场景的结合。
    - **≥ 85分 (薪资谈判级)**: 完美掌握 WHWS 模型。不仅懂原理，还能横向对比(Why)，并能主动分享实战踩坑经验(Scenarios)，主导对话节奏。

    【特殊情况处理】：
    如果【对话历史】非常短（例如只有 1-2 轮问答），且候选人主动结束或回答很少：
    1. 分数请给出 **5-15分** 之间的“参与分”。
    2. **评语必须包含**：“由于面试轮次过少，无法全面评估...” 字样。
    3. 这种情况下，Strengths 可以写“尚无足够数据评估”，Suggestions 可以建议“请尝试完成完整的 10 轮面试”。

    【输出格式要求】：
    1. 必须返回纯 JSON 格式。
    2. 不要使用 Markdown 标记。
    3. 结构如下：
    {
        "score": (0-100 整数),
        "comment": "简短犀利的综合评价，请指出他处于哪个层级（初级/进阶/专家）",
        "strengths": ["根据WHWS模型发现的亮点1", "亮点2"],
        "suggestions": ["针对缺失维度的具体建议1", "建议2"]
    }
    """

    full_prompt = f"{system_prompt}\n\n【对话历史】:\n{history_text}"

    try:
        response = client.models.generate_content(
            model="gemini-3-pro-preview",
            contents=full_prompt,
            config=types.GenerateContentConfig(
                temperature=0.3,  # 降低温度，让评分更客观稳定
                response_mime_type="application/json",
                max_output_tokens=65535,
            ),
        )

        raw_text = response.text
        clean_json = raw_text.replace("```json", "").replace("```", "").strip()
        data = json.loads(clean_json)

        return {
            "score": data.get("score", 60),
            "comment": data.get("comment", "暂无评价"),
            "strengths": data.get("strengths", []),
            "suggestions": data.get("suggestions", []),
        }

    except Exception as e:
        print(f"Report Generation Error: {e}")
        return {
            "score": 0,
            "comment": "AI 阅卷服务繁忙，请稍后重试",
            "strengths": [],
            "suggestions": [],
        }


def get_llm_response(messages: list) -> str:
    """
    非流式简单调用，供脚本或后台任务使用
    :param messages: [{"role": "user", "content": "..."}]
    :return: AI 的完整文本回复
    """
    if not client:
        return "Error: Gemini Client not initialized"

    try:
        # 取出最后一条用户消息的内容
        prompt = messages[-1]["content"]

        # 这里的 messages 格式可能包含 system prompt，但在简单脚本里我们简化处理
        # 直接调用生成内容
        response = client.models.generate_content(
            model="gemini-3-flash-preview",  # 用 Flash 模型比较快且便宜
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.7, max_output_tokens=65535
            ),
        )

        return response.text if response.text else ""

    except Exception as e:
        print(f"LLM Call Error: {e}")
        return ""
