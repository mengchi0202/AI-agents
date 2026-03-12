from __future__ import annotations
from typing import Any, Dict, List, Optional, TypedDict, Literal


NewsTrigger = Literal["qa", "digest", "refresh"]
NewsScope = Literal["industry", "macro", "general"]
QuestionType = Literal["term", "market_reasoning", "industry_impact", "general"]


class NewsState(TypedDict, total=False):
    # ---- Input ----
    user_id: str
    raw_text: str
    trigger: NewsTrigger  # qa | digest | refresh

    # ---- Router output ----
    intent: str  # e.g., "qa" / "digest"
    question_type: QuestionType
    scope: NewsScope
    need_news: bool
    need_kb: bool

    # ---- Fetch output ----
    # candidates: list of article dicts: {id,url,title,source,published_at,summary,content}
    candidates: List[Dict[str, Any]]

    # ---- Understand (IR) output ----
    # ir_items: list of enriched dicts: {article_id, event, why_it_matters, entities, tickers?, uncertainty}
    ir_items: List[Dict[str, Any]]

    # ---- Rank output ----
    hot_items: List[Dict[str, Any]]
    personalized_items: List[Dict[str, Any]]
    final_items: List[Dict[str, Any]]

    # ---- Knowledge/QA output ----
    kb_context: Optional[str]        # glossary hits or retrieved snippets
    answer_draft: Optional[str]      # raw draft from LLM

    # ---- Final output ----
    response_message: str
    error: Optional[str]

    # ---- Debug ----
    debug: Dict[str, Any]
