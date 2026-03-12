def presentation_node(state: dict) -> dict:
    parts = []

    if state.get("knowledge_content"):
        parts.append("📘 知識小補充\n" + state["knowledge_content"])

    if state.get("news_content"):
        parts.append("🗞️ 相關新聞\n" + state["news_content"])

    state["final_response"] = "\n\n".join(parts)
    return state
