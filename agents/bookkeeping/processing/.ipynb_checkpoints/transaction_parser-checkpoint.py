"""
Transaction Parser Node - LangGraph 版本（純 LLM）
使用 TAIDE 模型解析自然語言記帳輸入
"""
import json
import logging
from typing import Any, Dict

from ....agents.base import BookkeepingState
from ....models import get_taide_model

logger = logging.getLogger(__name__)


# ============================================================================
# LLM Prompt
# ============================================================================

PARSE_PROMPT = """你是一個專業的記帳助手，負責解析用戶的記帳輸入。
即使用戶有錯字、簡寫或口語化表達，你都要盡力理解真正的意思。

例如：
- 「麥噹噹」→ 麥當勞
- 「小七」→ 7-11
- 「全家喝了杯拿鐵」→ 商家:全家, 描述:拿鐵
- 「星八」→ 星巴克
- 「薪水入帳 45000」→ 收入, 金額:45000

請解析以下記帳內容：

用戶輸入：{user_input}

請以 JSON 格式回答，只回覆 JSON，不要任何其他文字：
{{
    "amount": 金額（純數字）,
    "transaction_type": "expense" 或 "income",
    "description": "簡短描述（2-10字，修正錯字後的版本）",
    "merchant": "商家名稱（修正錯字後的正確名稱，若無則 null）",
    "time_hint": "時間提示（如今天、午餐、晚餐，若無則 null）",
    "needs_time_clarification": true 或 false（是否需要追問用餐時段）
}}"""


# ============================================================================
# LLM 回應解析
# ============================================================================

def parse_llm_response(response: str, original_text: str) -> Dict[str, Any]:
    """解析 LLM 的 JSON 回應"""
    try:
        # 清理 markdown 格式
        cleaned = response.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.split("```")[1]
            if cleaned.startswith("json"):
                cleaned = cleaned[4:]
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]
        cleaned = cleaned.strip()

        # 嘗試找 JSON
        start = cleaned.find("{")
        end = cleaned.rfind("}") + 1
        if start != -1 and end > start:
            cleaned = cleaned[start:end]

        result = json.loads(cleaned)

        return {
            "amount": float(result.get("amount", 0)),
            "transaction_type": result.get("transaction_type", "expense"),
            "description": result.get("description", original_text[:20]),
            "merchant": result.get("merchant"),
            "time_hint": result.get("time_hint"),
            "needs_time_clarification": result.get("needs_time_clarification", False),
            "parse_confidence": 0.85,
        }

    except (json.JSONDecodeError, ValueError, KeyError) as e:
        logger.warning(f"JSON 解析失敗: {e}, 回應: {response[:200]}")
        return {
            "amount": 0,
            "transaction_type": "expense",
            "description": original_text[:20],
            "merchant": None,
            "time_hint": None,
            "needs_time_clarification": False,
            "parse_confidence": 0.0,
            "error": f"LLM 回應解析失敗: {str(e)}",
        }


# ============================================================================
# LangGraph Node
# ============================================================================

def transaction_parser_node(state: BookkeepingState) -> dict:
    """
    Transaction Parser Node（純 LLM 版）
    從 state['raw_text'] 用 TAIDE 解析交易資訊，寫回 state
    """
    text = state.get("raw_text", "")

    if not text:
        return {
            "error": "輸入文字為空",
            "parse_method": "none",
        }

    try:
        # 取得模型
        model = get_taide_model()
        if not model.is_loaded:
            model.load()

        # 呼叫 LLM
        prompt = PARSE_PROMPT.format(user_input=text)
        response = model.generate(prompt, temperature=0.1, max_new_tokens=256)

        # 解析回應
        parsed = parse_llm_response(response, text)

        # 檢查金額是否有效
        if parsed["amount"] <= 0:
            return {
                "error": f"無法從「{text}」解析出有效金額",
                "parse_method": "llm",
                "description": text[:20],
            }

        return {
            "amount": parsed["amount"],
            "transaction_type": parsed["transaction_type"],
            "description": parsed["description"],
            "time_hint": parsed["time_hint"],
            "merchant": parsed["merchant"],
            "parse_confidence": parsed["parse_confidence"],
            "parse_method": "llm",
        }

    except Exception as e:
        logger.error(f"Transaction Parser 錯誤: {e}")
        return {
            "error": f"解析失敗: {str(e)}",
            "parse_method": "llm",
        }
