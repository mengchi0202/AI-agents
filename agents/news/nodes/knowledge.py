from __future__ import annotations
from typing import Any, Dict
from src.models.taide import get_taide_model
from src.agents.news.state import NewsState


def news_knowledge_node(state: NewsState) -> Dict[str, Any]:
    raw_text = (state.get("raw_text") or "").strip()
    qtype = state.get("question_type") or "general"
    model = get_taide_model()

    # 先不做 RAG：直接用 task_configs 控制格式/語氣
    task_map = {
        "term": "finance_term_explain",
        "market_reasoning": "market_reasoning",
        "industry_impact": "industry_impact",
        "general": "finance_term_explain",
    }
    task_name = task_map.get(qtype, "finance_term_explain")

    prompt = (
        "請用繁體中文回答，避免投資建議與保證，必要時用「可能/通常/視情況」措辭。\n"
        f"問題類型：{qtype}\n"
        f"使用者問題：{raw_text}\n"
    )

    try:
        answer = model.generate_task(task_name, prompt)
        return {"answer_draft": answer, "debug": {**state.get("debug", {}), "knowledge": {"task": task_name}}}
    except Exception as e:
        return {"answer_draft": "（暫時無法產生答案）", "error": str(e)}
