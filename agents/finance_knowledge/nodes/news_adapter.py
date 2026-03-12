from __future__ import annotations
from typing import Any, Dict

from src.agents.finance_knowledge.state import FinanceState


def finance_to_news_adapter(state: FinanceState) -> FinanceState:
    """
    FinanceState -> NewsState (dict)
    只做 mapping，不做新聞處理。
    """
    if not state.get("run_news", False):
        return state

    news_state_in: Dict[str, Any] = {
        "user_id": state.get("user_id", "unknown"),
        "raw_text": state.get("raw_input", ""),
        "trigger": "qa",  # finance query 預設走 QA；若你要推播再改成 digest/refresh
        "debug": {
            "from_finance": {
                "user_level": state.get("user_level"),
                "user_preference": state.get("user_preference", []),
            }
        },
    }

    state["news_state_in"] = news_state_in

    dbg = state.get("debug") or {}
    dbg["news_adapter"] = {"mapped": True}
    state["debug"] = dbg
    return state


def run_news_subgraph(state: FinanceState) -> FinanceState:
    """
    在 Finance Graph 內執行 News 子圖：news_app.invoke(news_state)
    """
    if not state.get("run_news", False):
        return state

    news_state_in = state.get("news_state_in") or {}
    if not (news_state_in.get("raw_text") or "").strip():
        dbg = state.get("debug") or {}
        dbg["news_subgraph"] = {"skipped": "empty_raw_text"}
        state["debug"] = dbg
        return state

    # 延遲 import，避免 circular import
    from src.agents.news.graph import build_news_graph

    news_app = build_news_graph()
    news_out = news_app.invoke(news_state_in)

    state["news_state_out"] = news_out

    dbg = state.get("debug") or {}
    dbg["news_subgraph"] = {"ran": True}
    state["debug"] = dbg
    return state


def news_to_finance_adapter(state: FinanceState) -> FinanceState:
    """
    NewsState(out) -> FinanceState.news_content
    """
    if not state.get("run_news", False):
        return state

    news_out = state.get("news_state_out") or {}
    msg = (news_out.get("response_message") or "").strip()

    if msg:
        state["news_content"] = msg

    dbg = state.get("debug") or {}
    dbg["news_adapter"] = {**dbg.get("news_adapter", {}), "backfill": bool(msg)}
    state["debug"] = dbg
    return state
