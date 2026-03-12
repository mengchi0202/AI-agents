#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Category Classifier Node - LangGraph 版本
使用 TAIDE 模型分類交易
"""

import json
import logging
import sys
import os
from typing import Dict, Optional

# 添加專案根目錄到 Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))

logger = logging.getLogger(__name__)


# ============================================================================
# Import 處理
# ============================================================================

try:
    from ....models import get_taide_model
    from ....database.crud import get_all_categories, get_category_by_name
except (ImportError, ValueError):
    try:
        from src.models import get_taide_model
        from src.database.crud import get_all_categories, get_category_by_name
    except ImportError:
        logger.warning("無法導入模組，使用 Mock")
        
        def get_taide_model():
            class MockModel:
                is_loaded = True
                def load(self): pass
                def generate(self, prompt, **kwargs):
                    return '{"category_name": "食物飲料", "sub_category_name": "午餐", "reason": "速食餐廳"}'
            return MockModel()
        
        def get_all_categories():
            return [{"category_id": 1, "name": "食物飲料"}]
        
        def get_category_by_name(name):
            return {"category_id": 1, "name": "食物飲料"}


# ============================================================================
# LLM Prompt
# ============================================================================

CLASSIFY_PROMPT = """你是一個專業的記帳分類助手。根據交易資訊，判斷應該歸類到哪個分類。

交易資訊：
- 描述：{description}
- 金額：${amount}
- 商家：{merchant}

可用分類：
{categories}

請以 JSON 格式回答，只回覆 JSON：
{{
    "category_name": "分類名稱",
    "sub_category_name": "子分類名稱（如果有）",
    "reason": "分類原因（10字以內）"
}}

範例：
輸入：麥當勞 $159
輸出：{{"category_name": "食物飲料", "sub_category_name": "午餐", "reason": "速食餐廳"}}
"""


# ============================================================================
# LLM 回應解析
# ============================================================================

def parse_llm_response(response: str) -> Dict:
    """解析 LLM 回應"""
    try:
        text = response.strip()
        
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0]
        elif "```" in text:
            text = text.split("```")[1].split("```")[0]
        
        text = text.strip()
        
        start = text.find("{")
        end = text.rfind("}") + 1
        if start != -1 and end > start:
            text = text[start:end]
        
        result = json.loads(text)
        
        return {
            "category_name": result.get("category_name", ""),
            "sub_category_name": result.get("sub_category_name"),
            "reason": result.get("reason", ""),
        }
    
    except Exception as e:
        logger.warning(f"[Classifier] JSON 解析失敗: {e}")
        return {
            "category_name": "",
            "sub_category_name": None,
            "reason": "解析失敗",
        }


# ============================================================================
# Fallback 分類（關鍵字規則）
# ============================================================================

def classify_by_keywords(description: str, merchant: str = None) -> Dict:
    """關鍵字規則分類"""
    
    text = f"{description} {merchant or ''}".lower()
    
    keyword_map = {
        "食物飲料": ["食物", "飲料", "午餐", "晚餐", "早餐", "麥當勞", "星巴克", "便當", "餐廳", "咖啡"],
        "交通運輸": ["交通", "捷運", "公車", "計程車", "uber", "油錢", "停車"],
        "購物消費": ["購物", "買", "衣服", "鞋子", "包包", "網購"],
        "娛樂休閒": ["娛樂", "電影", "遊戲", "旅遊", "唱歌", "ktv"],
        "醫療保健": ["醫療", "看病", "藥", "健保", "診所", "醫院"],
        "教育學習": ["教育", "課程", "書", "學費", "補習"],
        "居住水電": ["房租", "水電", "瓦斯", "網路", "電話費"],
    }
    
    for category, keywords in keyword_map.items():
        for keyword in keywords:
            if keyword in text:
                return {
                    "category_name": category,
                    "reason": f"包含關鍵字：{keyword}"
                }
    
    return {
        "category_name": "其他支出",
        "reason": "無法辨識"
    }


# ============================================================================
# LangGraph Node
# ============================================================================

def category_classifier_node(state: dict) -> dict:
    """
    Category Classifier Node
    
    流程：
    1. 調用 LLM 分類
    2. 查詢資料庫獲取 category_id
    3. 如果失敗，使用關鍵字規則
    
    輸入: description, merchant, amount
    輸出: category_name, category_id
    """
    logger.info("[Classifier] 開始分類")
    
    if state.get("error"):
        logger.warning("[Classifier] ⚠️ 偵測到錯誤，跳過分類")
        return {}
    
    description = state.get("description", "")
    merchant = state.get("merchant", "")
    amount = state.get("amount", 0)
    
    logger.info(f"  描述: {description}")
    logger.info(f"  商家: {merchant}")
    
    try:
        # ====================================
        # Step 1: 取得可用分類
        # ====================================
        categories = get_all_categories()
        categories_text = "\n".join([f"- {cat['name']}" for cat in categories])
        
        # ====================================
        # Step 2: LLM 分類
        # ====================================
        try:
            model = get_taide_model()
            if not model.is_loaded:
                model.load()
            
            prompt = CLASSIFY_PROMPT.format(
                description=description,
                amount=amount,
                merchant=merchant or "未知",
                categories=categories_text
            )
            
            logger.info("[Classifier] 呼叫 TAIDE 模型...")
            response = model.generate(prompt, temperature=0.1, max_new_tokens=256)
            logger.info(f"[Classifier] LLM 回應: {response}")
            
            llm_result = parse_llm_response(response)
            category_name = llm_result["category_name"]
            
            if not category_name:
                raise ValueError("LLM 未返回分類名稱")
            
            method = "llm"
        
        except Exception as e:
            logger.warning(f"[Classifier] LLM 分類失敗，使用關鍵字規則: {e}")
            
            # Fallback 到關鍵字規則
            fallback_result = classify_by_keywords(description, merchant)
            category_name = fallback_result["category_name"]
            method = "keywords"
        
        # ====================================
        # Step 3: 查詢資料庫獲取 category_id
        # ====================================
        category = get_category_by_name(category_name)
        
        if category:
            category_id = category.get("category_id")
            category_name = category.get("name", category_name)
            logger.info(f"[Classifier] ✅ 分類完成: {category_name} (ID: {category_id})")
        else:
            category_id = None
            logger.warning(f"[Classifier] ⚠️ 未找到分類: {category_name}")
        
        return {
            "category_name": category_name,
            "category_id": category_id,
            "classify_method": method,
        }
    
    except Exception as e:
        logger.error(f"[Classifier] ❌ 分類失敗: {e}")
        import traceback
        traceback.print_exc()
        
        return {
            "category_name": "其他支出",
            "category_id": None,
            "classify_method": "error",
        }


# ============================================================================
# 測試函數
# ============================================================================

def test_category_classifier():
    """測試分類器"""
    print("=" * 60)
    print("Category Classifier 測試")
    print("=" * 60)
    
    test_cases = [
        {
            "description": "麥當勞",
            "merchant": "McDonald's",
            "amount": 159.0,
            "transaction_type": "expense"
        },
        {
            "description": "捷運卡加值",
            "merchant": None,
            "amount": 500.0,
            "transaction_type": "expense"
        },
        {
            "description": "買衣服",
            "merchant": "UNIQLO",
            "amount": 1500.0,
            "transaction_type": "expense"
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n【測試案例 {i}】")
        print(f"輸入: {test_case}")
        
        result = category_classifier_node(test_case)
        
        print(f"輸出:")
        print(f"  分類: {result.get('category_name')}")
        print(f"  ID: {result.get('category_id')}")
        print(f"  方法: {result.get('classify_method')}")
        print("-" * 60)


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    test_category_classifier()
