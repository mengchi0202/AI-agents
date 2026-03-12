import os
import numpy as np
from typing import Dict, Any, List

from sqlalchemy import create_engine, text
from sentence_transformers import SentenceTransformer


DB_URL = os.getenv("DB_URL")
if not DB_URL:
    raise ValueError("DB_URL is not set")

engine = create_engine(DB_URL, pool_pre_ping=True)

# embedding model
model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")


def embed_query(q: str) -> List[float]:
    vec = model.encode([q], normalize_embeddings=True)[0]
    return vec.astype(np.float32).tolist()


def rag_retriever(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Retrieve finance knowledge from kb_entries using pgvector similarity search.
    只負責 retrieval，不直接生成 knowledge_content。
    """

    raw_input = (state.get("raw_input") or "").strip()
    concepts = state.get("concepts") or []

    dbg = state.get("debug") or {}
    dbg.setdefault("rag_retriever", {})

    if not raw_input:
        state["rag_results"] = []
        state["retrieved_docs"] = []
        dbg["rag_retriever"] = {"mode": "skip", "reason": "empty_input"}
        state["debug"] = dbg
        return state

    # 簡單 query expansion：raw_input + concepts
    retrieval_query = raw_input
    if concepts:
        retrieval_query = f"{raw_input} {' '.join(concepts)}"

    query_vec = embed_query(retrieval_query)

    sql = text("""
        SELECT id, title, payload, doc,
               embedding <=> :query_vec AS distance
        FROM kb_entries
        ORDER BY embedding <=> :query_vec
        LIMIT 5
    """)

    try:
        with engine.begin() as conn:
            rows = conn.execute(sql, {"query_vec": query_vec}).mappings().all()

        results = [dict(r) for r in rows]

        # 單獨整理出 doc，給 executor 更方便使用
        retrieved_docs = []
        for r in results[:3]:
            doc = r.get("doc")
            if doc:
                retrieved_docs.append({
                    "id": r.get("id"),
                    "title": r.get("title"),
                    "doc": doc,
                    "distance": float(r.get("distance", 0.0)),
                })

        state["retrieval_query"] = retrieval_query
        state["rag_results"] = results
        state["retrieved_docs"] = retrieved_docs

        dbg["rag_retriever"] = {
            "mode": "vector_search",
            "retrieval_query": retrieval_query,
            "result_count": len(results),
            "top_ids": [r.get("id") for r in results[:3]],
        }
        state["debug"] = dbg
        return state

    except Exception as e:
        state["rag_results"] = []
        state["retrieved_docs"] = []
        dbg["rag_retriever"] = {
            "mode": "error",
            "error": str(e),
            "retrieval_query": retrieval_query,
        }
        state["debug"] = dbg
        return state