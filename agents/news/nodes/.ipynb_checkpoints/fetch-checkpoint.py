from __future__ import annotations
from typing import Any, Dict

from src.config import get_configs
from src.agents.news.state import NewsState
from src.mcp.tools.news_tools import fetch_rss, filter_taiwan_etf, dedup_articles


def news_fetch_node(state: NewsState) -> Dict[str, Any]:
    cfg = get_configs()["news"]
    rss_cfg = ((cfg.get("sources") or {}).get("rss") or {})
    enabled = bool(rss_cfg.get("enabled", False))
    feeds = rss_cfg.get("feeds") or []

    if not enabled or not feeds:
        return {
            "candidates": [],
            "debug": {**state.get("debug", {}), "fetch": {"enabled": enabled, "feeds": len(feeds)}},
        }

    # 1) 抓 RSS
    items = fetch_rss(feeds, per_feed_limit=80)

    # 2) 去重
    items = dedup_articles(items)

    # 3) 聚焦台股 ETF（用 news.yaml 的 defaults.keywords 控制）
    prefs = (cfg.get("preferences") or {}).get("defaults") or {}
    keywords = prefs.get("keywords") or []
    focused = filter_taiwan_etf(items, keywords=keywords if keywords else None)

    return {
        "candidates": focused,
        "debug": {**state.get("debug", {}), "fetch": {"mode": "rss", "total": len(items), "focused": len(focused)}},
    }
