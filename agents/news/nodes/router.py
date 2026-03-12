from __future__ import annotations
from typing import Any, Dict
import json

from src.models.taide import get_taide_model
from src.agents.news.state import NewsState


def _fallback_router(raw_text: str) -> Dict[str, Any]:
    t = raw_text.strip()

    # 非常簡單的 fallback 規則：先讓系統能跑
    if any(k in t for k in ["推播", "新聞", "熱門", "今天有什麼新聞", "給我新聞"]):
        return {
            "intent": "digest",
            "question_type": "general",
            "scope": "general",
            "need_news": True,
            "need_kb": False,
        }

    if any(k in t for k in ["什麼是", "名詞", "意思", "定義"]):
        return {
            "intent": "qa",
            "question_type": "term",
            "scope": "general",
            "need_news": False,
            "need_kb": True,
        }

    if any(k in t for k in ["為什麼", "原因", "漲", "跌", "漲停", "盤勢"]):
        return {
            "intent": "qa",
            "question_type": "market_reasoning",
            "scope": "macro",
            "need_news": True,
            "need_kb": True,
        }

    if any(k in t for k in ["產業", "供應鏈", "影響哪些", "會影響到什麼股", "科技最近發生"]):
        return {
            "intent": "qa",
            "question_type": "industry_impact",
            "scope": "industry",
            "need_news": True,
            "need_kb": True,
        }

    return {
        "intent": "qa",
        "question_type": "general",
        "scope": "general",
        "need_news": True,   # 保守：一般問題先嘗試查新聞
        "need_kb": True,
    }


def news_router_node(state: NewsState) -> Dict[str, Any]:
    raw_text = (state.get("raw_text") or "").strip()
    trigger = state.get("trigger") or "qa"

    # digest/refresh 直接走新聞流程
    if trigger in ("digest", "refresh"):
        return {
            "intent": "digest",
            "question_type": "general",
            "scope": "general",
            "need_news": True,
            "need_kb": False,
            "debug": {**state.get("debug", {}), "router": {"mode": "trigger", "trigger": trigger}},
        }

    # QA：優先用 LLM router（若你尚未加 task_configs.news_router，也會 fallback 到 inference default）
    model = get_taide_model()
    prompt = (
        "請判斷使用者問題要走哪種任務，並輸出 JSON：\n"
        "{intent: 'qa'|'digest', question_type: 'term'|'market_reasoning'|'industry_impact'|'general', "
        "scope: 'industry'|'macro'|'general', need_news: true/false, need_kb: true/false}\n"
        f"使用者輸入：{raw_text}"
    )

    try:
        out = model.generate_task("news_router", prompt)
        parsed = json.loads(out)
        # 最低限度防呆
        for k in ["intent", "question_type", "scope", "need_news", "need_kb"]:
            if k not in parsed:
                raise ValueError(f"missing key: {k}")
        parsed["debug"] = {**state.get("debug", {}), "router": {"mode": "llm", "raw": out}}
        return parsed
    except Exception:
        fb = _fallback_router(raw_text)
        fb["debug"] = {**state.get("debug", {}), "router": {"mode": "fallback"}}
        return fb

