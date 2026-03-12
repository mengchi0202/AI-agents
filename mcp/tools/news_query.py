from typing import Dict, Any, List
from datetime import datetime

def news_query(query: str, top_k: int = 3, market: str = "TW", focus: str = "ETF") -> Dict[str, Any]:
    now = datetime.utcnow().isoformat() + "Z"
    sample: List[Dict[str, Any]] = [
        {
            "title": f"（示意）台股/ETF 相關新聞：{query}",
            "url": "https://example.com/mock-news-1",
            "published_at": now,
            "source": "mock"
        },
        {
            "title": "（示意）ETF 資金流與市場情緒的白話解讀",
            "url": "https://example.com/mock-news-2",
            "published_at": now,
            "source": "mock"
        },
        {
            "title": "（示意）台股大盤波動與新手注意事項",
            "url": "https://example.com/mock-news-3",
            "published_at": now,
            "source": "mock"
        },
    ]
    return {"articles": sample[:top_k], "query": query, "top_k": top_k, "market": market, "focus": focus}
