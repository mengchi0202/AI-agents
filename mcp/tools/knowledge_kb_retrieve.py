from pathlib import Path
from typing import Dict, Any, List
import yaml

KB_PATH = Path("data/kb/finance_kb.yaml")

def knowledge_kb_retrieve(query: str, top_k: int = 3) -> Dict[str, Any]:
    data = yaml.safe_load(KB_PATH.read_text(encoding="utf-8"))
    entries: List[Dict[str, Any]] = data.get("entries", [])

    q = (query or "").lower()
    tokens = [t for t in q.replace("？", " ").replace("?", " ").split() if t]

    scored = []
    for e in entries:
        tags = e.get("tags", [])
        tags_text = " ".join(str(t) for t in tags)

        blob = (
            (str(e.get("title", "")) + " " +
            str(e.get("summary", "")) + " " +
            tags_text)
            .lower()
        )

        score = sum(1 for t in set(tokens) if t in blob)
        scored.append((score, e))

    scored.sort(key=lambda x: x[0], reverse=True)
    hits = [e for s, e in scored[:top_k] if s > 0]

    return {"hits": hits, "top_k": top_k, "query": query}
