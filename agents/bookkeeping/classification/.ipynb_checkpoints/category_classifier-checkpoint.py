#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Transaction Parser Node - 純 LLM 版本
使用 TAIDE 模型解析用戶輸入的交易資訊
"""

import json
import logging
import sys
import os
from typing import Dict, Optional
from datetime import datetime, timedelta

# 添加專案根目錄到 Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))

logger = logging.getLogger(__name__)


# ============================================================================
# Import 處理
# ============================================================================

try:
    from ....models import get_taide_model
except (ImportError, ValueError):
    try:
        from src.models import get_taide_model
    except ImportError:
        logger.warning("無法導入模型，使用 Mock")
        
        def get_taide_model():
            class MockModel:
                is_loaded = True
                def load(self): pass
                def generate(self, prompt, **kwargs):
                    return '''{
                        "amount": 159.0,
                        "transaction_type": "expense",
                        "description": "麥當勞",
                        "merchant": "McDonald's",
                        "time_hint": "today"
                    }'''
            return MockModel()


# ============================================================================
# LLM Prompt
# ============================================================================

PARSE_PROMPT = """你是一個專業的記帳解析助手。請解析用戶的記帳輸入，提取以下資訊：

用戶輸入：{raw_text}

請以 JSON 格式回答，只回覆 JSON，不要其他文字：
{{
    "amount": 金額（數字），
    "transaction_type": "expense" 或 "income"（支出或收入），
    "description": "簡短描述（去除金額後的主要內容）",
    "merchant": "商家名稱（如果有的話，否則 null）",
    "time_hint": "today" 或 "yesterday" 或 null（時間提示）
}}

解析規則：
1. 金額：提取數字部分，如果有小數點要保留
2. 類型：
   - 包含「收入、賺、薪水、獎金、紅包」等詞 → income
   - 其他 → expense（預設）
3. 描述：移除金額和貨幣符號後的主要內容
4. 商家：識別品牌名稱（如麥當勞、星巴克、全家等）
5. 時間：識別「昨天、今天」等時間詞

範例：
輸入：麥麥 159
輸出：{{"amount": 159.0, "transaction_type": "expense", "description": "麥當勞", "merchant": "McDonald's", "time_hint": "today"}}

輸入：昨天早餐 65
輸出：{{"amount": 65.0, "transaction_type": "expense", "description": "早餐", "merchant": null, "time_hint": "yesterday"}}

輸入：薪水 35000
輸出：{{"amount": 35000.0, "transaction_type": "income", "description": "薪水", "merchant": null, "time_hint": "today"}}
"""


# ============================================================================
# LLM 回應解析
# ============================================================================

def parse_llm_response(response: str) -> Dict:
    """
    解析 LLM 回應
    """
    try:
        text = response.strip()
        
        # 移除 Markdown code block
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0]
        elif "```" in text:
            text = text.split("```")[1].split("```")[0]
        
        text = text.strip()
        
        # 提取 JSON
        start = text.find("{")
        end = text.rfind("}") + 1
        if start != -1 and end > start:
            text = text[start:end]
        
        result = json.loads(text)
        
        return {
            "amount": float(result.get("amount", 0)),
            "transaction_type": result.get("transaction_type", "expense"),
            "description": result.get("description", ""),
            "merchant": result.get("merchant"),
            "time_hint": result.get("time_hint"),
        }
    
    except Exception as e:
        logger.error(f"[Parser] JSON 解析失敗: {e}")
        logger.error(f"[Parser] 原始回應: {response}")
        raise ValueError(f"解析失敗: {str(e)}")


# ============================================================================
# 時間處理
# ============================================================================

def process_time_hint(time_hint: Optional[str]) -> str:
    """
    根據時間提示計算實際日期
    """
    today = datetime.now().date()
    
    if time_hint == "yesterday":
        return (today - timedelta(days=1)).isoformat()
    elif time_hint == "today" or not time_hint:
        return today.isoformat()
    else:
        # 其他情況預設今天
        return today.isoformat()


# ============================================================================
# LangGraph Node
# ============================================================================

def transaction_parser_node(state: Dict) -> Dict:
    """
    Transaction Parser Node - 純 LLM 版本
    
    流程：
    1. 調用 TAIDE 模型解析用戶輸入
    2. 提取金額、類型、描述、商家等資訊
    3. 處理時間提示
    4. 返回結構化數據
    
    輸入: raw_text, user_id
    輸出: amount, transaction_type, description, merchant, transaction_date
    """
    logger.info("[Parser] 開始解析交易")
    
    raw_text = state.get("raw_text", "")
    
    if not raw_text or not raw_text.strip():
        logger.error("[Parser] ❌ 輸入為空")
        return {
            **state,
            "error": "請輸入交易資訊",
            "parse_confidence": 0.0,
            "parse_method": "failed"
        }
    
    logger.info(f"[Parser] 用戶輸入: {raw_text}")
    
    try:
        # ====================================
        # 調用 LLM 解析
        # ====================================
        model = get_taide_model()
        if not model.is_loaded:
            model.load()
        
        prompt = PARSE_PROMPT.format(raw_text=raw_text)
        
        logger.info("[Parser] 呼叫 TAIDE 模型...")
        response = model.generate(prompt, temperature=0.1, max_new_tokens=256)
        logger.info(f"[Parser] LLM 回應: {response}")
        
        # 解析回應
        parsed = parse_llm_response(response)
        
        # 驗證必要欄位
        if parsed["amount"] <= 0:
            logger.error("[Parser] ❌ 無法識別金額")
            return {
                **state,
                "error": "無法識別金額，請確認輸入格式",
                "parse_confidence": 0.0,
                "parse_method": "llm"
            }
        
        # 處理時間
        transaction_date = process_time_hint(parsed.get("time_hint"))
        
        logger.info(f"[Parser] ✅ 解析成功")
        logger.info(f"  金額: ${parsed['amount']}")
        logger.info(f"  類型: {parsed['transaction_type']}")
        logger.info(f"  描述: {parsed['description']}")
        logger.info(f"  商家: {parsed.get('merchant', '無')}")
        logger.info(f"  日期: {transaction_date}")
        
        return {
            **state,
            "amount": parsed["amount"],
            "transaction_type": parsed["transaction_type"],
            "description": parsed["description"],
            "merchant": parsed.get("merchant"),
            "time_hint": parsed.get("time_hint"),
            "transaction_date": transaction_date,
            "parse_confidence": 0.9,  # LLM 解析信心度
            "parse_method": "llm",
            "error": None
        }
    
    except Exception as e:
        logger.error(f"[Parser] ❌ 解析失敗: {e}")
        import traceback
        traceback.print_exc()
        
        return {
            **state,
            "error": f"解析錯誤: {str(e)}",
            "parse_confidence": 0.0,
            "parse_method": "failed"
        }


# ============================================================================
# 測試函數
# ============================================================================

def test_transaction_parser():
    """
    測試交易解析
    """
    print("=" * 60)
    print("Transaction Parser 測試（純 LLM）")
    print("=" * 60)
    
    test_cases = [
        {"raw_text": "麥麥 159", "user_id": 1},
        {"raw_text": "昨天捷運卡加值 500", "user_id": 1},
        {"raw_text": "薪水 35000", "user_id": 1},
        {"raw_text": "星巴克咖啡 150", "user_id": 1},
        {"raw_text": "買衣服 1500", "user_id": 1},
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n【測試案例 {i}】")
        print(f"輸入: {test_case['raw_text']}")
        
        result = transaction_parser_node(test_case)
        
        if result.get("error"):
            print(f"❌ 解析失敗: {result['error']}")
        else:
            print(f"✅ 解析成功:")
            print(f"  金額: ${result['amount']}")
            print(f"  類型: {result['transaction_type']}")
            print(f"  描述: {result['description']}")
            print(f"  商家: {result.get('merchant', '無')}")
            print(f"  日期: {result['transaction_date']}")
        
        print("-" * 60)


if __name__ == "__main__":
    # 設定 logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # 執行測試
    test_transaction_parser()