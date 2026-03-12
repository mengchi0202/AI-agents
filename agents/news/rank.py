from __future__ import annotations
from typing import Any, Dict, List, Tuple
from datetime import datetime

from src.config import get_configs
from src.agents.news.state import NewsState


def _score_hot(article: Dict[str, Any]) -> float:
    # MVP：只用 source_weight（RSS weight）做一個簡單分數
    return float(article.get("source_weight", 1.0))


def _score_personal(article: Dict[str, Any], keywords: List[str]) -> float:
    text = (article.get("title") or "") + " " + (article.get("summary") or "")
    hit = sum(1 for k in keywords if k and k in text)
    return float(article.get("source_weight", 1.0)) + hit * 2.0


def news_rank_node(state: NewsState) -> Dict[str, Any]:
    cfg = get_configs()["news"]
    candidates = state.get("candidates") or []

    hot_cfg = ((cfg.get("channels") or {}).get("hot") or {})
    per_cfg = ((cfg.get("channels") or {}).get("personalized") or {})
    hot_limit = int(hot_cfg.get("limit", 5))
    per_limit = int(per_cfg.get("limit", 5))

    prefs = (cfg.get("preferences") or {}).get("defaults") or {}
    keywords = prefs.get("keywords") or []

    hot_sorted = sorted(candidates, key=_score_hot, reverse=True)[:hot_limit]
    per_sorted = sorted(candidates, key=lambda a: _score_personal(a, keywords), reverse=True)[:per_limit]

    # final_items：先 hot 再 personalized 去重
    seen = set()
    final: List[Dict[str, Any]] = []
    for a in hot_sorted + per_sorted:
        aid = a.get("id")
        if aid in seen:
            continue
        seen.add(aid)
        final.append(a)

    return {
        "hot_items": hot_sorted,
        "personalized_items": per_sorted,
        "final_items": final,
        "debug": {**state.get("debug", {}), "rank": {"hot": len(hot_sorted), "personal": len(per_sorted), "final": len(final)}},
    }
