from __future__ import annotations
from typing import Any, Dict, List

from src.agents.news.state import NewsState
from src.mcp.tools.news_tools import compress_fallback
from src.models.taide import get_taide_model


def news_understand_node(state: NewsState) -> Dict[str, Any]:
    candidates = state.get("candidates") or []
    model = get_taide_model()

    if not candidates:
        return {"ir_items": [], "debug": {**state.get("debug", {}), "understand": {"count": 0}}}

    ir_items: List[Dict[str, Any]] = []
    for art in candidates[:10]:
        title = art.get("title", "") or ""
        summary = art.get("summary", "") or ""

        # mock/無模型：先做保底摘要（確保流程可測）
        if getattr(model, "_use_mock", False):
            rewrite = compress_fallback(title, summary, max_len=140)
            ir_items.append({"article_id": art.get("id"), "rewrite_summary": rewrite})
            continue

        # 未來接 TAIDE：用真正的「重寫摘要」
        prompt = (
            "請把下面新聞內容改寫成 1~2 句摘要（繁體中文），要忠於原意、不加料、不下投資建議。\n"
            f"標題：{title}\n"
            f"摘要/內文：{summary}\n"
        )
        rewrite = model.generate_task("news_summarize", prompt)
        ir_items.append({"article_id": art.get("id"), "rewrite_summary": rewrite.strip()})

    return {"ir_items": ir_items, "debug": {**state.get("debug", {}), "understand": {"count": len(ir_items)}}}
