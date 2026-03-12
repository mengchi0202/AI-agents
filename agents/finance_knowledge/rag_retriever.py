import os
import numpy as np
from typing import Dict, Any, List

from sqlalchemy import create_engine, text
from sentence_transformers import SentenceTransformer


DB_URL = os.getenv("DB_URL")
if not DB_URL:
    raise ValueError("DB_URL is not set")

engine = create_engine(DB_URL, pool_pre_ping=True)
model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")


def embed_query(q: str) -> List[float]:
    vec = model.encode([q], normalize_embeddings=True)[0]
    return vec.astype(np.float32).tolist()


def to_pgvector_literal(vec: List[float]) -> str:
    return "[" + ",".join(str(float(x)) for x in vec) + "]"


def rag_retriever(state: Dict[str, Any]) -> Dict[str, Any]:
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

    retrieval_query = raw_input
    if concepts:
        retrieval_query = f"{raw_input} {' '.join(concepts)}"

    query_vec = embed_query(retrieval_query)
    query_vec_literal = to_pgvector_literal(query_vec)

    sql = text("""
        SELECT id, title, payload, doc,
               embedding <=> CAST(:query_vec AS vector) AS distance
        FROM kb_entries
        ORDER BY embedding <=> CAST(:query_vec AS vector)
        LIMIT 5
    """)

    try:
        with engine.begin() as conn:
            rows = conn.execute(sql, {"query_vec": query_vec_literal}).mappings().all()

        results = [dict(r) for r in rows]

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