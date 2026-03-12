#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Budget Monitor Node - LangGraph 版本（LLM + 預算規則）
1. 查詢用戶該分類的月預算和已花費
2. 計算使用百分比和剩餘額度
3. LLM 判斷預算狀態並生成提醒
"""

import json
import logging
import sys
import os
from typing import Any, Dict, Optional

# 添加專案根目錄到 Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))

logger = logging.getLogger(__name__)


# ============================================================================
# Import 處理
# ============================================================================

try:
    # 嘗試相對導入
    from ....models import get_taide_model
    from ....database.crud import get_user_budget, get_category_spending
except (ImportError, ValueError):
    try:
        # 嘗試絕對導入
        from src.models import get_taide_model
        from src.database.crud import get_user_budget, get_category_spending
    except ImportError:
        logger.warning("無法導入模組，使用 Mock")
        
        # Mock 函數
        def get_taide_model():
            class MockModel:
                is_loaded = True
                def load(self): pass
                def generate(self, prompt, **kwargs):
                    return '{"budget_warning": "預算使用已達75%", "budget_level": "warning", "saving_tip": "建議減少非必要開支"}'
            return MockModel()
        
        def get_user_budget(user_id: int, category: str):
            return None
        
        def get_category_spending(user_id: int, category: str):
            return None


# ============================================================================
# Mock 預算數據（Fallback）
# ============================================================================

MOCK_BUDGETS = {
    "食物飲料": {"monthly_budget": 3000, "spent": 2500},
    "午餐": {"monthly_budget": 3000, "spent": 2500},
    "晚餐": {"monthly_budget": 4000, "spent": 2800},
    "早餐": {"monthly_budget": 1500, "spent": 900},
    "飲料": {"monthly_budget": 1000, "spent": 750},
    "交通運輸": {"monthly_budget": 2000, "spent": 1200},
    "購物消費": {"monthly_budget": 3000, "spent": 1500},
    "娛樂休閒": {"monthly_budget": 2000, "spent": 1800},
    "醫療保健": {"monthly_budget": 2000, "spent": 300},
    "教育學習": {"monthly_budget": 2000, "spent": 800},
    "居住水電": {"monthly_budget": 5000, "spent": 3200},
    "其他支出": {"monthly_budget": 3000, "spent": 1000},
}

# 整體月預算
MOCK_TOTAL_BUDGET = {
    "monthly_budget": 25000,
    "total_spent": 13750,
}


def get_budget_info(category_name: str, user_id: int = None) -> Optional[Dict]:
    """
    取得該分類的預算資訊
    
    優先順序：
    1. 從資料庫查詢用戶預算
    2. 使用 Mock 數據
    3. 返回 None
    """
    # 嘗試從資料庫查詢
    if user_id:
        try:
            budget = get_user_budget(user_id, category_name)
            if budget:
                spent = get_category_spending(user_id, category_name)
                logger.info(f"[Budget] 使用資料庫預算數據: {category_name}")
                return {
                    "monthly_budget": budget["amount"],
                    "spent": spent or 0
                }
        except Exception as e:
            logger.warning(f"[Budget] 查詢資料庫失敗: {e}")
    
    # 精確匹配 Mock
    if category_name in MOCK_BUDGETS:
        logger.info(f"[Budget] 使用 Mock 預算數據: {category_name}")
        return MOCK_BUDGETS[category_name]
    
    # 模糊匹配
    for key, budget in MOCK_BUDGETS.items():
        if key in category_name or category_name in key:
            logger.info(f"[Budget] 使用模糊匹配 Mock 數據: {key} → {category_name}")
            return budget
    
    logger.warning(f"[Budget] 無預算數據: {category_name}")
    return None


def get_total_budget(user_id: int = None) -> Dict:
    """
    取得整體月預算
    """
    # TODO: 從資料庫查詢
    return MOCK_TOTAL_BUDGET


# ============================================================================
# 預算計算
# ============================================================================

def calculate_budget_status(budget_info: Dict, new_amount: float) -> Dict:
    """
    計算加上這筆消費後的預算狀態
    
    返回：
    {
        "monthly_budget": 月預算,
        "already_spent": 記帳前已花費,
        "after_spent": 記帳後已花費,
        "remaining": 剩餘額度,
        "usage_pct": 使用百分比,
        "level": 預算等級
    }
    """
    monthly_budget = budget_info["monthly_budget"]
    already_spent = budget_info["spent"]
    after_spent = already_spent + new_amount
    remaining = monthly_budget - after_spent
    usage_pct = round(after_spent / monthly_budget * 100, 1) if monthly_budget > 0 else 0
    
    # 判斷等級
    if usage_pct >= 100:
        level = "exceeded"      # 超支
    elif usage_pct >= 90:
        level = "critical"      # 危險（90-100%）
    elif usage_pct >= 75:
        level = "warning"       # 警告（75-90%）
    elif usage_pct >= 50:
        level = "normal"        # 正常（50-75%）
    else:
        level = "healthy"       # 健康（<50%）
    
    return {
        "monthly_budget": monthly_budget,
        "already_spent": already_spent,
        "after_spent": after_spent,
        "remaining": remaining,
        "usage_pct": usage_pct,
        "level": level,
    }


# ============================================================================
# LLM Prompt
# ============================================================================

BUDGET_PROMPT = """你是一個專業的預算監控助手。根據以下預算狀況，給用戶簡短的提醒。

這筆交易：
- 描述：{description}
- 金額：${amount}
- 分類：{category}

該分類預算狀況：
- 月預算：${monthly_budget}
- 記帳前已花費：${already_spent}
- 記帳後已花費：${after_spent}
- 剩餘額度：${remaining}
- 使用百分比：{usage_pct}%
- 狀態：{level}

整體月預算：
- 總月預算：${total_budget}
- 總已花費：${total_spent}
- 總剩餘：${total_remaining}

請以 JSON 格式回答，只回覆 JSON，不要其他文字：
{{
    "budget_warning": "給用戶的預算提醒（30字以內，friendly 語氣。如果 healthy 則為 null）",
    "budget_level": "{level}",
    "saving_tip": "省錢小建議（20字以內，如果不需要則為 null）"
}}

範例：
狀態 exceeded：{{"budget_warning": "本月{category}預算已超支 ${over}元", "budget_level": "exceeded", "saving_tip": "建議減少非必要開支"}}
狀態 critical：{{"budget_warning": "本月{category}預算僅剩 ${remaining}元", "budget_level": "critical", "saving_tip": "接近預算上限，請謹慎消費"}}
狀態 healthy：{{"budget_warning": null, "budget_level": "healthy", "saving_tip": null}}
"""

BUDGET_PROMPT_NO_BUDGET = """你是一個專業的預算監控助手。這個分類目前沒有設定預算。

這筆交易：
- 描述：{description}
- 金額：${amount}
- 分類：{category}

請以 JSON 格式回答，只回覆 JSON：
{{
    "budget_warning": null,
    "budget_level": "no_budget",
    "saving_tip": "建議為「{category}」設定每月預算，更好掌握開銷"
}}"""


# ============================================================================
# LLM 回應解析
# ============================================================================

def parse_llm_response(response: str) -> Dict:
    """
    解析 LLM 回應的 JSON
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
            "budget_warning": result.get("budget_warning"),
            "budget_level": result.get("budget_level", "unknown"),
            "saving_tip": result.get("saving_tip"),
        }
    
    except Exception as e:
        logger.warning(f"[Budget] LLM 回應解析失敗: {e}")
        logger.warning(f"[Budget] 原始回應: {response[:200]}")
        
        return {
            "budget_warning": None,
            "budget_level": "unknown",
            "saving_tip": None,
        }


# ============================================================================
# LangGraph Node
# ============================================================================

def budget_monitor_node(state: dict) -> dict:
    """
    Budget Monitor Node（LLM + 預算規則）
    
    流程：
    1. 查詢用戶預算設定
    2. 計算預算使用狀況
    3. 調用 LLM 生成預算提醒
    4. 返回預算狀態
    
    輸入: amount, category_name, description, transaction_type, user_id
    輸出: budget_warning, budget_level, budget_usage_pct, budget_remaining
    """
    logger.info("[Budget] 開始預算檢查")
    
    # 如果前面有錯誤，跳過
    if state.get("error"):
        logger.warning("[Budget] ⚠️ 偵測到錯誤，跳過預算檢查")
        return {}
    
    amount = state.get("amount", 0)
    category = state.get("category_name", "其他支出")
    description = state.get("description", "")
    transaction_type = state.get("transaction_type", "expense")
    user_id = state.get("user_id")
    
    logger.info(f"  金額: ${amount}")
    logger.info(f"  分類: {category}")
    logger.info(f"  類型: {transaction_type}")
    
    # 金額驗證
    if amount <= 0:
        logger.warning("[Budget] ⚠️ 金額無效，跳過預算檢查")
        return {
            "budget_warning": None,
            "budget_level": "skip",
        }
    
    # 只有支出才需要檢查預算
    if transaction_type == "income":
        logger.info("[Budget] ℹ️ 收入交易，跳過預算檢查")
        return {
            "budget_warning": None,
            "budget_level": "income",
        }
    
    try:
        # ====================================
        # Step 1: 查預算
        # ====================================
        budget_info = get_budget_info(category, user_id)
        total_budget = get_total_budget(user_id)
        
        # ====================================
        # Step 2: 取得模型
        # ====================================
        model = get_taide_model()
        if not model.is_loaded:
            model.load()
        
        # ====================================
        # Step 3: 組合 prompt 並調用 LLM
        # ====================================
        if budget_info:
            # 計算預算狀態
            status = calculate_budget_status(budget_info, amount)
            total_remaining = total_budget["monthly_budget"] - total_budget["total_spent"]
            
            logger.info(f"[Budget] 預算狀態:")
            logger.info(f"  使用率: {status['usage_pct']}%")
            logger.info(f"  等級: {status['level']}")
            logger.info(f"  剩餘: ${status['remaining']}")
            
            # 組合 prompt
            prompt = BUDGET_PROMPT.format(
                description=description,
                amount=amount,
                category=category,
                monthly_budget=status["monthly_budget"],
                already_spent=status["already_spent"],
                after_spent=status["after_spent"],
                remaining=status["remaining"],
                usage_pct=status["usage_pct"],
                level=status["level"],
                total_budget=total_budget["monthly_budget"],
                total_spent=total_budget["total_spent"],
                total_remaining=total_remaining,
            )
            method = "llm+rules"
        
        else:
            # 無預算設定
            logger.warning(f"[Budget] ⚠️ 未設定預算")
            status = {
                "level": "no_budget",
                "usage_pct": 0,
                "remaining": 0
            }
            
            prompt = BUDGET_PROMPT_NO_BUDGET.format(
                description=description,
                amount=amount,
                category=category,
            )
            method = "llm_only"
        
        # ====================================
        # Step 4: LLM 判斷
        # ====================================
        logger.info("[Budget] 呼叫 TAIDE 模型...")
        response = model.generate(prompt, temperature=0.1, max_new_tokens=256)
        logger.info(f"[Budget] LLM 回應: {response}")
        
        # 解析回應
        llm_result = parse_llm_response(response)
        
        logger.info(f"[Budget] ✅ 預算檢查完成")
        if llm_result["budget_warning"]:
            logger.info(f"  警告: {llm_result['budget_warning']}")
        if llm_result["saving_tip"]:
            logger.info(f"  建議: {llm_result['saving_tip']}")
        
        return {
            "budget_warning": llm_result["budget_warning"],
            "budget_level": status["level"],
            "budget_usage_pct": status.get("usage_pct", 0),
            "budget_remaining": status.get("remaining", 0),
            "budget_method": method,
        }
    
    except Exception as e:
        logger.error(f"[Budget] ❌ 預算檢查失敗: {e}")
        import traceback
        traceback.print_exc()
        
        return {
            "budget_warning": None,
            "budget_level": "error",
            "budget_method": "error",
        }


# ============================================================================
# 測試函數
# ============================================================================

def test_budget_monitor():
    """
    測試預算監控
    """
    print("=" * 60)
    print("Budget Monitor 測試")
    print("=" * 60)
    
    test_cases = [
        {
            "amount": 150.0,
            "category_name": "食物飲料",
            "description": "午餐",
            "transaction_type": "expense",
            "user_id": 1
        },
        {
            "amount": 800.0,
            "category_name": "食物飲料",
            "description": "聚餐",
            "transaction_type": "expense",
            "user_id": 1
        },
        {
            "amount": 35000.0,
            "category_name": "薪資收入",
            "description": "薪水",
            "transaction_type": "income",
            "user_id": 1
        },
        {
            "amount": 5000.0,
            "category_name": "購物消費",
            "description": "買衣服",
            "transaction_type": "expense",
            "user_id": 1
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n【測試案例 {i}】")
        print(f"輸入: {test_case}")
        
        result = budget_monitor_node(test_case)
        
        print(f"輸出:")
        print(f"  預算等級: {result.get('budget_level')}")
        print(f"  使用率: {result.get('budget_usage_pct')}%")
        print(f"  剩餘: ${result.get('budget_remaining')}")
        print(f"  警告: {result.get('budget_warning')}")
        print(f"  方法: {result.get('budget_method')}")
        print("-" * 60)


if __name__ == "__main__":
    # 設定 logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # 執行測試
    test_budget_monitor()