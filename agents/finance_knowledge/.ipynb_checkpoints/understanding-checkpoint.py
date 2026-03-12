from __future__ import annotations
from typing import Any, Dict, List, Tuple
import json

from src.models.taide import get_taide_model
from .state import FinanceState


def _default_understanding(state: FinanceState) -> Dict[str, Any]:
    """
    fallback：保守抽取
    - concepts 至少不為空/None
    - need_news 只有明確新聞需求才為 True
    """
    text = (state.get("raw_input") or "").strip()
    concepts: List[str] = []

    text_upper = text.upper()

    if "ETF" in text_upper:
        concepts.append("ETF")
    if "0050" in text:
        concepts.append("0050")
    if "升息" in text:
        concepts.append("升息")
    if "降息" in text:
        concepts.append("降息")
    if "通膨" in text:
        concepts.append("通膨")
    if "科技股" in text:
        concepts.append("科技股")
    if "台股" in text:
        concepts.append("台股")

    news_keywords = [
        "新聞",
        "最新消息",
        "近期消息",
        "最近新聞",
        "近期新聞",
        "新聞摘要",
        "有沒有",
        "發生什麼事",
        "最近怎麼了",
    ]
    need_news = any(k in text for k in news_keywords)

    return {
        "concepts": concepts[:5],
        "need_news": bool(need_news),
        "reason": ["fallback_keywords_strict_news"],
    }


def _validate_understanding_json(obj: Dict[str, Any]) -> Tuple[bool, List[str]]:
    errors: List[str] = []
    if "concepts" not in obj:
        errors.append("missing_key:concepts")
    if "need_news" not in obj:
        errors.append("missing_key:need_news")

    if "concepts" in obj and not isinstance(obj["concepts"], list):
        errors.append("concepts_not_list")
    if "concepts" in obj and isinstance(obj["concepts"], list):
        if any(not isinstance(x, str) for x in obj["concepts"]):
            errors.append("concepts_item_not_str")

    if "need_news" in obj and not isinstance(obj["need_news"], bool):
        errors.append("need_news_not_bool")

    return (len(errors) == 0), errors


def understanding_node(state: FinanceState) -> FinanceState:
    """
    Understanding Node（LLM 抽取）
    - 抽取 concepts（關鍵概念）
    - 判斷 need_news（是否真的明確要求近期新聞/事件）
    - 防呆：JSON parse 失敗 -> fallback
    """
    raw = (state.get("raw_input") or "").strip()

    dbg = state.get("debug") or {}
    dbg.setdefault("understanding", {})

    if not raw:
        fb = _default_understanding(state)
        state["concepts"] = fb["concepts"]
        state["need_news"] = fb["need_news"]
        dbg["understanding"] = {"mode": "fallback", "reason": ["empty_input"]}
        state["debug"] = dbg
        return state

    model = get_taide_model()
    task_name = "finance_understanding"

    prompt = (
        "你是金融多代理系統的理解模組（Understanding），只負責抽取結構化資訊，輸出 JSON，不要解釋。\n"
        "請從使用者輸入中抽取最重要的 0~5 個金融概念（concepts），並判斷是否需要新聞（need_news）。\n\n"
        "規則：\n"
        "- concepts 要用繁體中文、短詞（例如：ETF、升息、殖利率、通膨、台股ETF、0050）\n"
        "- 只有當使用者明確要求『新聞、最新消息、近期事件、新聞整理、新聞摘要』時，need_news 才設為 true\n"
        "- 若只是問市場看法、前景、影響、概念解釋，預設設為 false\n"
        "- 不要因為問題可能和時事有關，就自動設為 true\n\n"
        "請輸出 JSON（只能輸出 JSON，不能有多餘文字）：\n"
        "{\n"
        '  "concepts": ["..."],\n'
        '  "need_news": true | false,\n'
        '  "reason": ["..."]\n'
        "}\n\n"
        f"使用者輸入：{raw}\n"
    )

    try:
        out = model.generate_task(task_name, prompt)
        parsed = json.loads(out)
        ok, errs = _validate_understanding_json(parsed)
        if not ok:
            raise ValueError("invalid_understanding_json:" + ",".join(errs))

        concepts_raw: List[str] = [x.strip() for x in parsed["concepts"] if isinstance(x, str)]
        concepts: List[str] = []
        seen = set()
        for c in concepts_raw:
            if not c or c in seen:
                continue
            seen.add(c)
            concepts.append(c)
            if len(concepts) >= 5:
                break

        state["concepts"] = concepts
        state["need_news"] = bool(parsed["need_news"])

        dbg["understanding"] = {
            "mode": "llm",
            "task": task_name,
            "raw": out,
            "concepts": concepts,
            "need_news": parsed["need_news"],
            "reason": parsed.get("reason", []),
        }
        state["debug"] = dbg
        return state

    except Exception as e:
        fb = _default_understanding(state)
        state["concepts"] = fb["concepts"]
        state["need_news"] = fb["need_news"]
        dbg["understanding"] = {
            "mode": "fallback",
            "error": str(e),
            "reason": fb.get("reason", []),
        }
        state["debug"] = dbg
        return state