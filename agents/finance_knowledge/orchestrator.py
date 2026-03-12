from __future__ import annotations
from typing import Any, Dict, List, Literal, Tuple
import json
import re

from src.models.taide import get_taide_model
from .state import FinanceState

Intent = Literal["knowledge", "news", "mixed"]
Tone = Literal["simple", "normal"]


# =========================
# Helpers
# =========================

NEWS_KEYWORDS = [
    "新聞", "最新", "最近", "消息", "動態", "事件",
    "發生什麼", "近況", "今天", "本週", "這幾天",
    "有沒有相關新聞", "有沒有新聞", "相關新聞",
]

KNOWLEDGE_HINT_KEYWORDS = [
    "是什麼", "什麼是", "差異", "影響", "原因", "意思",
    "如何", "怎麼", "為什麼", "風險", "概念", "原理",
]


def _safe_strip(text: Any) -> str:
    return str(text).strip() if text is not None else ""


def _extract_json_object(text: str) -> Dict[str, Any]:
    """
    盡量從模型輸出中抽出第一個合法 JSON object。
    避免模型前後多吐說明文字時 json.loads 直接炸掉。
    """
    text = _safe_strip(text)
    if not text:
        raise ValueError("empty_response")

    # 1) 先直接 parse
    try:
        obj = json.loads(text)
        if isinstance(obj, dict):
            return obj
    except Exception:
        pass

    # 2) 抓第一個 {...}
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        candidate = match.group(0)
        obj = json.loads(candidate)
        if isinstance(obj, dict):
            return obj

    raise ValueError("no_valid_json_object_found")


def _has_news_signal(text: str) -> bool:
    text = _safe_strip(text)
    return any(k in text for k in NEWS_KEYWORDS)


def _has_knowledge_signal(text: str) -> bool:
    text = _safe_strip(text)
    return any(k in text for k in KNOWLEDGE_HINT_KEYWORDS)


def _rule_based_router(state: FinanceState) -> Dict[str, Any]:
    """
    當 LLM router 不穩時的保底規則。
    原則：knowledge-first，只有明確新聞需求才開 news。
    """
    raw = _safe_strip(state.get("raw_input"))
    user_level = _safe_strip(state.get("user_level")) or "beginner"

    tone: Tone = "simple" if user_level == "beginner" else "normal"

    has_news = _has_news_signal(raw)
    has_knowledge = _has_knowledge_signal(raw)

    if has_news and has_knowledge:
        intent: Intent = "mixed"
    elif has_news:
        # 即使是新聞查詢，多半仍需要金融知識補充，先走 mixed 比 news 穩
        intent = "mixed"
    else:
        intent = "knowledge"

    return {
        "intent": intent,
        "need_knowledge": True,
        "need_news": bool(has_news),
        "tone": tone,
        "reason": ["rule_based_router"],
    }


def _default_router(state: FinanceState) -> Dict[str, Any]:
    """
    最保守 fallback：
    - knowledge-first
    - 只有明確新聞語意才 need_news=True
    """
    base = _rule_based_router(state)
    base["reason"] = ["fallback_default_knowledge_first"]
    return base


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


# =========================
# Main Node
# =========================

def unified_orchestrator(state: FinanceState) -> FinanceState:
    """
    F0: Unified Orchestrator（LLM Router）

    只負責 routing decision，不做內容回答。
    輸出：
    - intent: knowledge / news / mixed
    - tone: simple / normal
    - need_knowledge / need_news

    設計原則：
    1. knowledge-first
    2. 只有明確新聞語意才開 news
    3. LLM 不穩時退回 rule-based fallback
    """
    raw = _safe_strip(state.get("raw_input"))
    user_level = _safe_strip(state.get("user_level")) or "beginner"
    prefs = state.get("user_preference") or []

    dbg = state.get("debug") or {}
    dbg.setdefault("orchestrator", {})

    # 空輸入直接 fallback
    if not raw:
        fb = _default_router(state)
        state["intent"] = fb["intent"]
        state["tone"] = fb["tone"]
        state["need_news"] = fb["need_news"]
        dbg["orchestrator"] = {
            "mode": "fallback",
            "reason": ["empty_input"],
            "resolved": fb,
        }
        state["debug"] = dbg
        return state

    # 如果是明顯的新聞查詢，先記錄 rule signal
    has_news_signal = _has_news_signal(raw)
    has_knowledge_signal = _has_knowledge_signal(raw)

    model = get_taide_model()
    task_name = "finance_router"

    prompt = f"""
你是金融多代理系統的 Router。
你的工作只有一件事：判斷這個問題應該走 knowledge、news 或 mixed。
你只能輸出一個合法 JSON object，不能有任何額外文字、註解、markdown、說明。

判斷規則：
1. knowledge：偏金融概念解釋、名詞、原理、差異、影響機制
2. news：偏近期消息、最新事件、今天/最近發生什麼
3. mixed：同時需要金融知識與近期新聞

額外要求：
- 系統預設採 knowledge-first
- 只有在使用者明確提到「新聞 / 最新 / 最近 / 消息 / 事件 / 今天 / 本週」等近期資訊時，need_news 才應該是 true
- 如果只是一般金融知識問答，need_news 必須是 false
- beginner 使用者 tone 請偏 simple，其餘可用 normal

你必須輸出這個格式的 JSON：
{{
  "intent": "knowledge",
  "need_knowledge": true,
  "need_news": false,
  "tone": "simple",
  "reason": ["..."]
}}

使用者程度：{user_level}
使用者偏好：{prefs}
使用者輸入：{raw}
""".strip()

    try:
        out = model.generate_task(
            task_name,
            prompt,
            temperature=0.0,
            max_new_tokens=256,
        )

        parsed = _extract_json_object(out)
        ok, errs = _validate_router_json(parsed)
        if not ok:
            raise ValueError("invalid_router_json:" + ",".join(errs))

        # 額外保底：
        # 若模型說不需要新聞，但 query 明顯有新聞語意，強制修正 need_news
        need_news = bool(parsed["need_news"]) or has_news_signal

        # 若有明確新聞語意但模型仍給 knowledge，保守修成 mixed
        intent = parsed["intent"]
        if has_news_signal and intent == "knowledge":
            intent = "mixed"

        state["intent"] = intent
        state["tone"] = parsed["tone"]
        state["need_news"] = need_news

        dbg["orchestrator"] = {
            "mode": "llm",
            "task": task_name,
            "raw_output": out,
            "parsed": parsed,
            "resolved": {
                "intent": intent,
                "need_knowledge": bool(parsed["need_knowledge"]),
                "need_news": need_news,
                "tone": parsed["tone"],
            },
            "signals": {
                "has_news_signal": has_news_signal,
                "has_knowledge_signal": has_knowledge_signal,
            },
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
            "resolved": fb,
            "signals": {
                "has_news_signal": has_news_signal,
                "has_knowledge_signal": has_knowledge_signal,
            },
        }
        state["debug"] = dbg
        return state