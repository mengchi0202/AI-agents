from __future__ import annotations
from typing import Any, Dict, List, Literal, Tuple
import json

from src.models.taide import get_taide_model
from .state import FinanceState

Intent = Literal["knowledge", "news", "mixed"]
Tone = Literal["simple", "normal"]


def _default_router(state: FinanceState) -> Dict[str, Any]:
    """
    極保守 fallback：
    預設走金融知識，不主動開新聞。
    """
    user_level = (state.get("user_level") or "beginner").strip()
    tone: Tone = "simple" if user_level == "beginner" else "normal"

    return {
        "intent": "knowledge",
        "need_knowledge": True,
        "need_news": False,
        "tone": tone,
        "reason": ["fallback_default_knowledge_first"],
    }


def _validate_router_json(obj: Dict[str, Any]) -> Tuple[bool, List[str]]:
    errors: List[str] = []
    for k in ["intent", "need_knowledge", "need_news", "tone"]:
        if k not in obj:
            errors.append(f"missing_key:{k}")

    if "intent" in obj and obj["intent"] not in ("knowledge", "news", "mixed"):
        errors.append("bad_intent")
    if "tone" in obj and obj["tone"] not in ("simple", "normal"):
        errors.append("bad_tone")

    if "need_knowledge" in obj and not isinstance(obj["need_knowledge"], bool):
        errors.append("need_knowledge_not_bool")
    if "need_news" in obj and not isinstance(obj["need_news"], bool):
        errors.append("need_news_not_bool")

    return (len(errors) == 0), errors


def unified_orchestrator(state: FinanceState) -> FinanceState:
    """
    F0: Unified Orchestrator（LLM Router）
    - 不做內容回答，只做 routing decision
    - 輸出：intent / tone / need_news
    - 新策略：金融知識優先，只有明確要求新聞時才開 news
    """
    raw = (state.get("raw_input") or "").strip()
    user_level = (state.get("user_level") or "beginner").strip()
    prefs = state.get("user_preference") or []

    dbg = state.get("debug") or {}
    dbg.setdefault("orchestrator", {})

    if not raw:
        fb = _default_router(state)
        state["intent"] = fb["intent"]
        state["tone"] = fb["tone"]
        state["need_news"] = fb["need_news"]
        dbg["orchestrator"] = {"mode": "fallback", "reason": ["empty_input"]}
        state["debug"] = dbg
        return state

    model = get_taide_model()
    task_name = "finance_router"

    prompt = (
        "你是金融多代理系統的路由器（Router），只負責輸出 JSON，不要解釋。\n"
        "請根據使用者輸入判斷要走哪種路徑：\n"
        "- knowledge：偏金融概念解釋、名詞說明、機制分析、投資教學\n"
        "- news：使用者明確要求新聞、最新消息、近期事件整理、新聞摘要\n"
        "- mixed：同時明確需要概念解釋與新聞事件\n\n"
        "重要規則：\n"
        "- 預設優先判為 knowledge\n"
        "- 只有在使用者明確提到『新聞、最新消息、近期事件、最近新聞、新聞摘要、有沒有某某新聞』時，才可判為 news 或 mixed\n"
        "- 若只是問『前景如何、股市如何、會不會影響』，優先判為 knowledge，不要因為可能涉及時事就直接開新聞\n\n"
        "請輸出 JSON（只能輸出 JSON，不能有多餘文字）：\n"
        "{\n"
        '  "intent": "knowledge" | "news" | "mixed",\n'
        '  "need_knowledge": true | false,\n'
        '  "need_news": true | false,\n'
        '  "tone": "simple" | "normal",\n'
        '  "reason": ["..."]\n'
        "}\n\n"
        f"使用者程度：{user_level}\n"
        f"使用者偏好：{prefs}\n"
        f"使用者輸入：{raw}\n"
    )

    try:
        out = model.generate_task(task_name, prompt)
        parsed = json.loads(out)

        ok, errs = _validate_router_json(parsed)
        if not ok:
            raise ValueError("invalid_router_json:" + ",".join(errs))

        state["intent"] = parsed["intent"]
        state["tone"] = parsed["tone"]
        state["need_news"] = bool(parsed["need_news"])

        dbg["orchestrator"] = {
            "mode": "llm",
            "task": task_name,
            "raw": out,
            "intent": parsed["intent"],
            "need_knowledge": parsed["need_knowledge"],
            "need_news": parsed["need_news"],
            "tone": parsed["tone"],
            "reason": parsed.get("reason", []),
        }
        state["debug"] = dbg
        return state

    except Exception as e:
        fb = _default_router(state)
        state["intent"] = fb["intent"]
        state["tone"] = fb["tone"]
        state["need_news"] = fb["need_news"]

        dbg["orchestrator"] = {
            "mode": "fallback",
            "error": str(e),
            "reason": fb.get("reason", []),
        }
        state["debug"] = dbg
        return state