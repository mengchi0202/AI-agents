from __future__ import annotations
from typing import Any, Dict, List, Optional
import hashlib
import re

def _hash(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()[:16]


def fetch_rss(feeds: List[Dict[str, Any]], per_feed_limit: int = 80) -> List[Dict[str, Any]]:
    """
    讀 RSS feeds，回傳候選文章列表。
    每篇文章格式：
    {id,url,title,source,source_weight,published_at,summary,content}
    """
    items: List[Dict[str, Any]] = []
    if not feeds:
        return items

    try:
        import feedparser  # type: ignore
    except Exception:
        # 沒裝 feedparser 就回空（不要炸）
        return items

    for f in feeds:
        url = f.get("url")
        name = f.get("name", "rss")
        weight = float(f.get("weight", 1.0))
        if not url:
            continue

        d = feedparser.parse(url)
        for e in getattr(d, "entries", [])[:per_feed_limit]:
            link = getattr(e, "link", "") or ""
            title = getattr(e, "title", "") or ""
            published = getattr(e, "published", "") or ""
            summary = getattr(e, "summary", "") or ""

            article_id = _hash(link or (title + published))
            items.append(
                {
                    "id": article_id,
                    "url": link,
                    "title": title,
                    "source": name,
                    "source_weight": weight,
                    "published_at": published,
                    "summary": summary,
                    "content": None,
                }
            )

    return items


_ETF_CODE_RE = re.compile(r"\b(00\d{2,3}|01\d{2,3})\b")  # 粗抓：0050/00878/00919...（可再調）


def filter_taiwan_etf(articles: List[Dict[str, Any]], keywords: Optional[List[str]] = None) -> List[Dict[str, Any]]:
    """
    聚焦台股 ETF：用關鍵字 + 代碼格式過濾。
    """
    if not articles:
        return []

    # 你可以在 news.yaml 放 defaults.keywords 來控制（例如 ETF/0050/00878/...）
    kw = keywords or [
        "ETF", "台股ETF", "台灣ETF", "元大", "國泰", "群益", "復華",
        "0050", "0056", "00878", "00919", "00891", "00929",
        "高股息", "市值型", "加權指數", "配息", "除息",
    ]

    out: List[Dict[str, Any]] = []
    for a in articles:
        text = f"{a.get('title','')} {a.get('summary','')}".upper()
        hit_kw = any(k.upper() in text for k in kw)
        hit_code = bool(_ETF_CODE_RE.search(text))
        if hit_kw or hit_code:
            out.append(a)
    return out


def dedup_articles(articles: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    去重：用 url 或 title hash。
    """
    seen = set()
    out: List[Dict[str, Any]] = []
    for a in articles:
        key = a.get("url") or (a.get("title") or "")
        if not key:
            continue
        if key in seen:
            continue
        seen.add(key)
        out.append(a)
    return out


def compress_fallback(title: str, summary: str, max_len: int = 140) -> str:
    """
    沒 LLM 時的保底摘要：不是截字，而是把 title + summary 做簡單重組與壓縮。
    （嚴格說仍是 extractive/heuristic，但先保證能跑；未來接 TAIDE 取代）
    """
    t = (title or "").strip()
    s = (summary or "").strip()
    if not s:
        return t[:max_len]
    # 簡單：優先用 summary 前段，前面加上 title 提示
    merged = f"{t}｜{s}"
    merged = re.sub(r"\s+", " ", merged).strip()
    return merged[:max_len]
