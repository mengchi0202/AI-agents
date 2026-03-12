from src.models.taide import get_taide_model


def knowledge_executor(state: dict) -> dict:
    if not state.get("run_knowledge"):
        return state

    query = (state.get("raw_input") or "").strip()
    concepts = state.get("concepts") or []
    rag_results = state.get("rag_results") or []
    retrieved_docs = state.get("retrieved_docs") or []
    user_level = (state.get("user_level") or "beginner").strip()
    tone = (state.get("tone") or "simple").strip()

    # 優先使用 retriever 已經整理好的 retrieved_docs
    docs_for_context = []
    if retrieved_docs:
        for item in retrieved_docs[:3]:
            doc = item.get("doc")
            if doc:
                docs_for_context.append(doc)
    else:
        # fallback：若沒有 retrieved_docs，就從 rag_results 裡抽 doc
        for r in rag_results[:3]:
            doc = r.get("doc")
            if doc:
                docs_for_context.append(doc)

    context = "\n\n---\n\n".join(docs_for_context).strip()
    concepts_text = ", ".join(concepts) if concepts else "未明確抽取到概念"

    if context:
        prompt = f"""
你是一位給使用者看的理財老師，請根據以下金融知識內容回答問題。

【使用者程度】
{user_level}

【回覆風格】
{tone}

【使用者問題】
{query}

【抽取到的概念】
{concepts_text}

【檢索到的金融知識內容】
{context}

請用繁體中文回答，要求：
1. 優先根據檢索到的知識內容回答，不要憑空補充
2. 若使用者是 beginner 或 tone=simple，請用更白話、生活化的方式解釋
3. 可以用條列整理重點
4. 若知識內容不足，請明確說明不確定處
5. 若適合，可補充簡單例子或風險提醒
"""
    else:
        prompt = f"""
你是一位給使用者看的理財老師。

【使用者程度】
{user_level}

【回覆風格】
{tone}

【使用者問題】
{query}

【抽取到的概念】
{concepts_text}

請用繁體中文回答，要求：
1. 用白話方式解釋，避免過度專業術語
2. 若使用者是 beginner 或 tone=simple，請多用生活化例子
3. 若資訊不足，請明確說明不確定處
4. 可用條列方式整理重點
"""

    model = get_taide_model()
    answer = model.generate(prompt)

    state["knowledge_content"] = answer
    return state