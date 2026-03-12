from .state import FinanceState


def domain_coordinator(state: FinanceState) -> FinanceState:
    """
    決定要不要跑 Knowledge / News
    - 預設以金融知識為主
    - 只有 intent 指向 news/mixed 且 need_news=True 時，才真的跑 news
    """
    intent = state.get("intent", "knowledge")
    need_news = bool(state.get("need_news", False))

    state["run_knowledge"] = intent in ["knowledge", "mixed"]
    state["run_news"] = (intent in ["news", "mixed"]) and need_news

    dbg = state.get("debug") or {}
    dbg["coordinator"] = {
        "intent": intent,
        "need_news": need_news,
        "run_knowledge": state["run_knowledge"],
        "run_news": state["run_news"],
    }
    state["debug"] = dbg

    return state