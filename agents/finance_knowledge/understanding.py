from __future__ import annotations
from typing import Any, Dict, List, Tuple
import re

from src.models.taide import get_taide_model
from src.utils.json_utils import extract_json_object
from .state import FinanceState


# =========================
# Fallback Lexicon
# =========================

FALLBACK_CONCEPT_RULES = [
    ("ETF", "ETF"),
    ("0050", "0050"),
    ("0056", "0056"),
    ("00878", "00878"),
    ("00919", "00919"),
    ("台股ETF", "台股ETF"),
    ("高股息", "高股息ETF"),
    ("市值型", "市值型ETF"),
    ("債券ETF", "債券ETF"),
    ("債券", "債券"),
    ("美債", "美債"),
    ("公債", "公債"),
    ("公司債", "公司債"),
    ("升息", "升息"),
    ("降息", "降息"),
    ("通膨", "通膨"),
    ("殖利率", "殖利率"),
    ("配息", "配息"),
    ("總報酬", "總報酬"),
    ("費用率", "費用率"),
    ("追蹤誤差", "追蹤誤差"),
    ("淨值", "淨值"),
    ("折溢價", "折溢價"),
    ("波動", "市場波動"),
    ("風險", "投資風險"),
    ("分散", "分散投資"),
    ("定期定額", "定期定額"),
    ("科技股", "科技股"),
    ("半導體", "半導體"),
    ("AI", "AI"),
    ("人工智慧", "AI"),
    ("台股", "台股"),
    ("美股", "美股"),
    ("台積電", "台積電"),
    ("聯發科", "聯發科"),
    ("景氣循環", "景氣循環"),
]


STRICT_NEWS_PATTERNS = [
    r"最近.*新聞",
    r"最新.*新聞",
    r"相關新聞",
    r"有沒有.*新聞",
    r"今天.*新聞",
    r"本週.*新聞",
    r"近期.*新聞",
    r"最近.*消息",
    r"最新.*消息",
    r"近期.*消息",
    r"最近.*發生什麼",
    r"最近怎麼了",
    r"新聞摘要",
    r"新聞整理",
]


# =========================
# Helpers
# =========================

def _safe_strip(x: Any) -> str:
    return str(x).strip() if x is not None else ""


def _strict_need_news(text: str) -> bool:
    text = _safe_strip(text)
    return any(re.search(p, text) for p in STRICT_NEWS_PATTERNS)


def _fallback_extract_concepts(text: str) -> List[str]:
    text = _safe_strip(text)
    concepts: List[str] = []
    seen = set()

    text_upper = text.upper()

    for keyword, normalized in FALLBACK_CONCEPT_RULES:
        target = text_upper if keyword.upper() == keyword else text
        key = keyword.upper() if keyword.upper() == keyword else keyword

        if key in target and normalized not in seen:
            seen.add(normalized)
            concepts.append(normalized)

        if len(concepts) >= 5:
            break

    return concepts


def _default_understanding(state: FinanceState) -> Dict[str, Any]:
    """
    fallback：保守抽取
    - concepts 至少不為空/None
    - need_news 只有明確新聞需求才為 True
    """
    text = _safe_strip(state.get("raw_input"))
    concepts = _fallback_extract_concepts(text)
    need_news = _strict_need_news(text)

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


# =========================
# Main Node
# =========================

def understanding_node(state: FinanceState) -> FinanceState:
    """
    Understanding Node（金融理解層）
    目的：
    - 抽取最重要的金融概念，供後續 RAG 檢索與回答使用
    - 判斷是否真的需要新聞查詢
    - 不直接回答問題，只做語意理解
    """
    raw = _safe_strip(state.get("raw_input"))

    dbg = state.get("debug") or {}
    dbg.setdefault("understanding", {})

    if not raw:
        fb = _default_understanding(state)
        state["concepts"] = fb["concepts"]
        state["need_news"] = fb["need_news"]
        dbg["understanding"] = {
            "mode": "fallback",
            "reason": ["empty_input"],
            "resolved": fb,
        }
        state["debug"] = dbg
        return state

    model = get_taide_model()
    task_name = "finance_understanding"

    prompt = f"""
你是金融知識系統的 Understanding 模組，也是金融問題語意分析專家。
你的工作不是回答問題，而是抽取「最有助於後續知識檢索與答案生成」的結構化資訊。

你只能輸出一個合法 JSON object，不能有任何額外文字、解釋、markdown、註解。

任務：
1. 從使用者輸入抽取 0~5 個最重要的金融 concepts
2. 判斷是否真的需要近期新聞（need_news）

concepts 抽取規則：
- 優先保留金融專有名詞、商品名稱、Ticker、ETF代碼、宏觀因子、產業詞
- 盡量用短詞，不要整句
- 使用繁體中文或原始代碼，例如：ETF、0050、升息、通膨、債券ETF、台股、科技股
- 不要抽太泛的詞，例如：問題、投資、市場、東西
- concepts 是給後續 RAG 檢索用，所以要偏「可檢索、可對應知識條目」的詞

need_news 判斷規則：
- 只有使用者明確要求「新聞 / 最新消息 / 最近消息 / 近期新聞 / 新聞整理 / 新聞摘要 / 最近發生什麼」時才設為 true
- 如果只是問概念、差異、影響、原因、風險、前景、機制，預設設為 false
- 不要因為問題可能跟時事有關，就自動設為 true

你必須輸出以下 JSON 格式：
{{
  "concepts": ["ETF", "升息"],
  "need_news": false,
  "reason": ["..."]
}}

使用者輸入：{raw}
""".strip()

    try:
        out = model.generate_task(
            task_name,
            prompt,
            temperature=0.0,
            max_new_tokens=256,
        )

        parsed = extract_json_object(out)
        ok, errs = _validate_understanding_json(parsed)
        if not ok:
            raise ValueError("invalid_understanding_json:" + ",".join(errs))

        concepts_raw: List[str] = [
            x.strip() for x in parsed["concepts"] if isinstance(x, str)
        ]

        concepts: List[str] = []
        seen = set()
        for c in concepts_raw:
            if not c or c in seen:
                continue
            seen.add(c)
            concepts.append(c)
            if len(concepts) >= 5:
                break

        # rule-based 保底修正
        fallback_need_news = _strict_need_news(raw)
        need_news = bool(parsed["need_news"]) or fallback_need_news

        # 若模型 concept 抽得太差，補 fallback
        if not concepts:
            concepts = _fallback_extract_concepts(raw)

        state["concepts"] = concepts
        state["need_news"] = need_news

        dbg["understanding"] = {
            "mode": "llm",
            "task": task_name,
            "raw_output": out,
            "parsed": parsed,
            "resolved": {
                "concepts": concepts,
                "need_news": need_news,
            },
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
            "resolved": fb,
        }
        state["debug"] = dbg
        return state