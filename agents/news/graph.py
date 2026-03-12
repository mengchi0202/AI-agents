from __future__ import annotations
from typing import Literal

from langgraph.graph import StateGraph, END  # 若 import error，貼錯誤我幫你改成你版本的寫法

from src.agents.news.state import NewsState
from src.agents.news.nodes.router import news_router_node
from src.agents.news.nodes.fetch import news_fetch_node
from src.agents.news.nodes.understand import news_understand_node
from src.agents.news.rank import news_rank_node
from src.agents.news.nodes.knowledge import news_knowledge_node
from src.agents.news.nodes.present import news_present_node


def _route(state: NewsState) -> Literal["digest_flow", "qa_flow"]:
    intent = state.get("intent") or "qa"
    return "digest_flow" if intent == "digest" else "qa_flow"


def build_news_graph():
    g = StateGraph(NewsState)

    # nodes
    g.add_node("router", news_router_node)

    # digest flow
    g.add_node("fetch", news_fetch_node)
    g.add_node("understand", news_understand_node)
    g.add_node("rank", news_rank_node)

    # qa flow
    g.add_node("knowledge", news_knowledge_node)

    # final
    g.add_node("present", news_present_node)

    # entry
    g.set_entry_point("router")

    # branching
    g.add_conditional_edges("router", _route, {
        "digest_flow": "fetch",
        "qa_flow": "knowledge",
    })

    # digest edges
    g.add_edge("fetch", "understand")
    g.add_edge("understand", "rank")
    g.add_edge("rank", "present")

    # qa edges
    g.add_edge("knowledge", "present")

    # end
    g.add_edge("present", END)

    app = g.compile()   
    return app
