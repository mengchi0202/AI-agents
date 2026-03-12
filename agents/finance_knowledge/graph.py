from __future__ import annotations
from typing import Literal

from langgraph.graph import StateGraph, END

from .state import FinanceState
from .orchestrator import unified_orchestrator
from .understanding import understanding_node
from .coordinator import domain_coordinator
from .knowledge_executor import knowledge_executor
from .presentation import presentation_node
from .rag_retriever import rag_retriever

from .nodes.news_adapter import (
    finance_to_news_adapter,
    run_news_subgraph,
    news_to_finance_adapter,
)


def _route_after_coordinator(state: FinanceState) -> Literal["knowledge_only", "news_only", "both", "presentation"]:
    k = bool(state.get("run_knowledge", False))
    n = bool(state.get("run_news", False))

    if k and n:
        return "both"
    if k:
        return "knowledge_only"
    if n:
        return "news_only"
    return "presentation"


def _route_after_knowledge(state: FinanceState) -> Literal["go_news", "go_presentation"]:
    return "go_news" if state.get("run_news", False) else "go_presentation"


def build_finance_graph():
    g = StateGraph(FinanceState)

    # ---- Control plane ----
    g.add_node("orchestrator", unified_orchestrator)
    g.add_node("understanding", understanding_node)
    g.add_node("coordinator", domain_coordinator)

    # ---- RAG retrieval ----
    g.add_node("rag_retriever", rag_retriever)

    # ---- Knowledge domain ----
    g.add_node("knowledge_domain", knowledge_executor)

    # ---- News domain (subgraph wrapper) ----
    g.add_node("news_adapter_in", finance_to_news_adapter)
    g.add_node("news_domain", run_news_subgraph)
    g.add_node("news_adapter_out", news_to_finance_adapter)

    # ---- Presentation / merge ----
    g.add_node("presentation", presentation_node)

    # ---- Entry ----
    g.set_entry_point("orchestrator")

    # ---- Base pipeline ----
    g.add_edge("orchestrator", "understanding")
    g.add_edge("understanding", "coordinator")

    # ---- Coordinator routing ----
    g.add_conditional_edges(
        "coordinator",
        _route_after_coordinator,
        {
            "knowledge_only": "rag_retriever",
            "news_only": "news_adapter_in",
            "both": "rag_retriever",
            "presentation": "presentation",
        },
    )

    # ---- RAG -> Knowledge ----
    g.add_edge("rag_retriever", "knowledge_domain")

    # ---- After Knowledge: mixed -> news, else -> presentation ----
    g.add_conditional_edges(
        "knowledge_domain",
        _route_after_knowledge,
        {
            "go_news": "news_adapter_in",
            "go_presentation": "presentation",
        },
    )

    # ---- News flow ----
    g.add_edge("news_adapter_in", "news_domain")
    g.add_edge("news_domain", "news_adapter_out")
    g.add_edge("news_adapter_out", "presentation")

    # ---- End ----
    g.add_edge("presentation", END)

    return g.compile()