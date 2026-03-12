from .state import FinanceState


def domain_coordinator(state: FinanceState) -> FinanceState:
    """
    決定要不要跑 Knowledge / News
    """
    intent = state.get("intent", "knowledge")
    need_news = bool(state.get("need_news", False))

    run_knowledge = intent in ["knowledge", "mixed"]
    run_news = intent in ["news", "mixed"] or need_news

    state["run_knowledge"] = run_knowledge
    state["run_news"] = run_news

    dbg = state.get("debug") or {}
    dbg["coordinator"] = {
        "intent": intent,
        "need_news": need_news,
        "run_knowledge": run_knowledge,
        "run_news": run_news,
    }
    state["debug"] = dbg

    return state