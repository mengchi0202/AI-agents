from __future__ import annotations
from typing import Any, Dict, List

from src.models.taide import get_taide_model
from src.agents.news.state import NewsState


def news_present_node(state: NewsState) -> Dict[str, Any]:
    intent = state.get("intent") or "qa"
    model = get_taide_model()

    if intent == "digest":
        items = state.get("final_items") or []
        ir = {x.get("article_id"): x for x in (state.get("ir_items") or [])}

        # 準備給 LLM / fallback 的輸入（簡短）
        lines: List[str] = []
        for i, a in enumerate(items[:10], start=1):
            aid = a.get("id")
            title = a.get("title", "") or "（無標題）"
            src = a.get("source", "") or "unknown"
            why = (ir.get(aid) or {}).get("rewrite_summary", "") or ""
            if why:
                lines.append(f"{i}. [{src}] {title}\n   為何重要：{why}".strip())
            else:
                lines.append(f"{i}. [{src}] {title}".strip())

        # ✅ Mock 模式：不呼叫 LLM，避免 TAIDE mock 回交易 JSON 汙染
        if getattr(model, "_use_mock", False):
            if lines:
                msg = "📌 今日新聞（Mock）\n" + "\n".join(lines)
            else:
                msg = "📌 今日新聞（Mock）\n（目前沒有抓到新聞，之後接上抓取功能會出現列表）"
            return {"response_message": msg}

        # 非 mock：用 LLM compose 推播（失敗就 fallback）
        prompt = (
            "你是新聞推播助理，請用繁體中文、語氣親切但不說教，整理成推播訊息。\n"
            "格式：先一段總覽，再列出條列，每則一句重點。\n"
            "可以適量 emoji。\n\n"
            + "\n".join(lines)
        )

        try:
            msg = model.generate_task("news_push_compose", prompt)
        except Exception:
            # fallback：不用 LLM 也能顯示
            if lines:
                msg = "📌 今日新聞\n" + "\n".join(lines)
            else:
                msg = "📌 今日新聞\n（目前沒有抓到新聞）"

        return {"response_message": msg}

    # QA 模式：present 只負責把 knowledge node 的 answer_draft 帶出去
    answer = (state.get("answer_draft") or "").strip()
    if not answer:
        answer = "我目前沒有足夠資訊回答，你可以再補充想看的產業/時間範圍或關鍵字。"

    return {"response_message": answer}
