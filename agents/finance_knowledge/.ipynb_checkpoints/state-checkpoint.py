from typing import TypedDict, List, Optional, Dict, Any


class FinanceState(TypedDict, total=False):

    # =========================
    # User Input
    # =========================
    user_id: str
    raw_input: str

    user_level: str               # beginner / normal
    user_preference: List[str]    # ["ETF", "台股"]

    # =========================
    # Understanding Layer
    # =========================
    intent: str                   # knowledge / news / mixed
    tone: str                     # simple / normal

    concepts: List[str]           # extracted finance concepts
    need_news: bool

    question_type: Optional[str]  # definition / comparison / market_reasoning / risk / general

    # query used for RAG retrieval
    retrieval_query: Optional[str]

    # =========================
    # Coordinator Decisions
    # =========================
    run_knowledge: bool
    run_news: bool

    # =========================
    # RAG Retrieval
    # =========================
    rag_results: Optional[List[Dict[str, Any]]]

    # simplified documents passed to executor
    retrieved_docs: Optional[List[Dict[str, Any]]]

    # =========================
    # Knowledge Execution
    # =========================
    knowledge_content: Optional[str]

    # =========================
    # News Domain
    # =========================
    news_state_in: Optional[Dict[str, Any]]
    news_state_out: Optional[Dict[str, Any]]

    news_content: Optional[str]

    # =========================
    # Final Response
    # =========================
    final_response: Optional[str]

    # =========================
    # Debug / Error
    # =========================
    debug: Optional[Dict[str, Any]]
    error: Optional[str]