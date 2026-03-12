from typing import Dict, Any, List

try:
    from src.mcp.tools.news_tools import fetch_rss, dedup_articles
except Exception:
    fetch_rss = None
    dedup_articles = None


DEFAULT_FEEDS = [
    "https://news.cnyes.com/rss/news/cat/headline",
]


def _fallback_items(keywords: List[str]) -> List[Dict[str, Any]]:
    kw_text = "、".join(keywords) if keywords else "相關主題"
    return [
        {
            "article_id": "mock-1",
            "title": f"{kw_text} 近期市場新聞整理（mock）",
            "summary": f"目前尚未接上正式新聞來源，這是 {kw_text} 的示意新聞摘要。",
            "source": "mock",
            "url": "",
        }
    ]


def news_fetch_node(state: Dict[str, Any]) -> Dict[str, Any]:
    keywords = state.get("keywords") or []

    dbg = state.get("debug") or {}
    dbg.setdefault("fetch", {})

    try:
        if fetch_rss is None:
            items = _fallback_items(keywords)
            state["candidates"] = items
            dbg["fetch"] = {"mode": "mock", "count": len(items)}
            state["debug"] = dbg
            return state

        items = fetch_rss(DEFAULT_FEEDS)

        if dedup_articles is not None:
            items = dedup_articles(items)

        if keywords:
            filtered = []
            for item in items:
                text = f"{item.get('title', '')} {item.get('summary', '')}"
                if any(k in text for k in keywords):
                    filtered.append(item)
            items = filtered or items[:10]
        else:
            items = items[:10]

        state["candidates"] = items
        dbg["fetch"] = {"mode": "rss", "count": len(items), "keywords": keywords}
        state["debug"] = dbg
        return state

    except Exception as e:
        items = _fallback_items(keywords)
        state["candidates"] = items
        dbg["fetch"] = {"mode": "fallback", "error": str(e), "count": len(items)}
        state["debug"] = dbg
        return state