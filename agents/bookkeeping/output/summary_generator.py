#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Summary Generator Node - LangGraph 版本
彙整記帳流程所有結果，用 TAIDE 生成友善的回覆訊息
"""

import json
import logging
import sys
import os
from typing import Dict

# 添加專案根目錄到 Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))

logger = logging.getLogger(__name__)


# ============================================================================
# Import 處理
# ============================================================================

try:
    # 嘗試相對導入
    from ....models import get_taide_model
except (ImportError, ValueError):
    try:
        # 嘗試絕對導入
        from src.models import get_taide_model
    except ImportError:
        logger.warning("無法導入模型，使用 Mock")
        
        # Mock 函數
        def get_taide_model():
            class MockModel:
                is_loaded = True
                def load(self): pass
                def generate(self, prompt, **kwargs):
                    return "✅ 已記錄：午餐 $150（食物飲料）"
            return MockModel()


# ============================================================================
# LLM Prompt
# ============================================================================

SUMMARY_PROMPT = """你是一個友善的記帳助手。根據以下記帳結果，生成一段簡短、口語化的回覆訊息給用戶。

記帳結果：
- 描述：{description}
- 金額：${amount}
- 類型：{transaction_type}
- 分類：{category_name}
- 商家：{merchant}
- 是否異常：{is_anomaly}
- 異常原因：{anomaly_reason}
- 預算狀態：{budget_level}
- 預算提醒：{budget_warning}
- 預算使用：{budget_usage_pct}%
- 預算剩餘：${budget_remaining}
- 儲存成功：{db_success}

請生成一段回覆訊息，要求：
1. 第一行用 ✅ 確認記帳成功（包含金額、分類）
2. 如果有異常，用 ⚠️ 提醒
3. 如果預算狀態是 warning/critical/exceeded，用 🟡/🔴 提醒預算
4. 語氣友善、簡潔，像朋友聊天
5. 總共不超過 3 行

只回覆訊息本身，不要 JSON，不要額外說明。

範例：
✅ 已記錄：午餐 $150（食物飲料）
🟡 本月食物飲料預算已使用 75%，注意控制哦！
"""

SUMMARY_PROMPT_ERROR = """你是一個友善的記帳助手。記帳過程發生錯誤，請生成一段簡短的錯誤提示。

錯誤資訊：{error}

請用友善的語氣告訴用戶記帳失敗，並建議重新輸入。不超過 2 行。
只回覆訊息本身，不要 JSON，不要額外說明。

範例：
❌ 記帳失敗：無法識別金額
請重新輸入，例如「午餐 150」
"""


# ============================================================================
# Fallback（如果 LLM 失敗，用規則生成）
# ============================================================================

def generate_fallback_summary(state: dict) -> str:
    """
    當 LLM 失敗時，用簡單規則生成回覆
    
    這是最後的保險機制，確保用戶總能得到回覆
    """
    amount = state.get("amount", 0)
    category = state.get("category_name", "其他")
    description = state.get("description", "消費")
    tx_type = state.get("transaction_type", "expense")
    is_anomaly = state.get("is_anomaly", False)
    budget_level = state.get("budget_level", "")
    budget_usage_pct = state.get("budget_usage_pct", 0)
    budget_remaining = state.get("budget_remaining", 0)
    
    # 基本確認
    if tx_type == "income":
        msg = f"✅ 已記錄收入：{description} +${amount}（{category}）"
    else:
        msg = f"✅ 已記錄：{description} ${amount}（{category}）"
    
    # 異常提醒
    if is_anomaly:
        reason = state.get("anomaly_reason", "金額偏高")
        severity = state.get("anomaly_severity", "medium")
        
        if severity == "high":
            msg += f"\n⚠️ 注意：{reason}"
        elif severity == "medium":
            msg += f"\n💡 提醒：{reason}"
    
    # 預算提醒
    if budget_level == "exceeded":
        msg += f"\n🔴 本月{category}預算已超支！已使用 {budget_usage_pct:.0f}%"
    elif budget_level == "critical":
        remaining_text = f"剩餘 ${budget_remaining:.0f}" if budget_remaining > 0 else "已用完"
        msg += f"\n🔴 本月{category}預算即將用完！{remaining_text}"
    elif budget_level == "warning":
        msg += f"\n🟡 本月{category}預算已使用 {budget_usage_pct:.0f}%，注意控制"
    
    return msg


# ============================================================================
# LangGraph Node
# ============================================================================

def summary_generator_node(state: dict) -> dict:
    """
    Summary Generator Node（TAIDE LLM）
    
    流程：
    1. 檢查是否有錯誤
    2. 調用 TAIDE 生成友善回覆
    3. 如果 LLM 失敗，使用 Fallback
    4. 返回最終訊息
    
    輸入: 所有 state 欄位
    輸出: response_message
    """
    logger.info("[Summary] 開始生成回覆訊息")
    
    # ====================================
    # 情況 1: 有錯誤
    # ====================================
    if state.get("error"):
        logger.warning(f"[Summary] ⚠️ 偵測到錯誤: {state['error']}")
        
        try:
            model = get_taide_model()
            if not model.is_loaded:
                model.load()
            
            prompt = SUMMARY_PROMPT_ERROR.format(error=state["error"])
            
            logger.info("[Summary] 呼叫 TAIDE 生成錯誤訊息...")
            response = model.generate(prompt, temperature=0.3, max_new_tokens=128)
            message = response.strip()
            
            logger.info(f"[Summary] ✅ 錯誤訊息生成完成")
            return {"response_message": message}
        
        except Exception as e:
            logger.error(f"[Summary] ❌ LLM 生成錯誤訊息失敗: {e}")
            return {"response_message": f"❌ 記帳失敗：{state['error']}\n請重新輸入，例如「午餐 150」"}
    
    # ====================================
    # 情況 2: DB 儲存失敗
    # ====================================
    if not state.get("db_success", False):
        logger.error("[Summary] ❌ DB 儲存失敗")
        return {"response_message": "❌ 記帳儲存失敗，請稍後再試"}
    
    # ====================================
    # 情況 3: 正常流程，生成摘要
    # ====================================
    try:
        model = get_taide_model()
        if not model.is_loaded:
            model.load()
        
        # 組合 prompt
        prompt = SUMMARY_PROMPT.format(
            description=state.get("description", "消費"),
            amount=state.get("amount", 0),
            transaction_type="收入" if state.get("transaction_type") == "income" else "支出",
            category_name=state.get("category_name", "其他"),
            merchant=state.get("merchant") or "未知",
            is_anomaly="是" if state.get("is_anomaly") else "否",
            anomaly_reason=state.get("anomaly_reason") or "無",
            budget_level=state.get("budget_level", "無預算"),
            budget_warning=state.get("budget_warning") or "無",
            budget_usage_pct=state.get("budget_usage_pct", 0),
            budget_remaining=state.get("budget_remaining", 0),
            db_success="是" if state.get("db_success") else "否",
        )
        
        logger.info("[Summary] 呼叫 TAIDE 生成摘要...")
        response = model.generate(prompt, temperature=0.3, max_new_tokens=256)
        message = response.strip()
        
        logger.info(f"[Summary] LLM 回應長度: {len(message)} 字元")
        
        # ====================================
        # 驗證 LLM 回應品質
        # ====================================
        
        # 檢查 1: 長度是否合理
        if len(message) < 5:
            logger.warning("[Summary] ⚠️ LLM 回應過短，使用 Fallback")
            message = generate_fallback_summary(state)
        
        elif len(message) > 300:
            logger.warning("[Summary] ⚠️ LLM 回應過長，使用 Fallback")
            message = generate_fallback_summary(state)
        
        # 檢查 2: 是否誤返回 JSON
        elif message.strip().startswith("{") or message.strip().startswith("["):
            logger.warning("[Summary] ⚠️ LLM 回應為 JSON 格式，使用 Fallback")
            message = generate_fallback_summary(state)
        
        # 檢查 3: 是否包含基本確認符號
        elif "✅" not in message and "❌" not in message:
            logger.warning("[Summary] ⚠️ LLM 回應缺少確認符號，使用 Fallback")
            message = generate_fallback_summary(state)
        
        logger.info(f"[Summary] ✅ 摘要生成完成")
        logger.info(f"[Summary] 訊息:\n{message}")
        
        return {"response_message": message}
    
    except Exception as e:
        logger.error(f"[Summary] ❌ Summary Generator 錯誤: {e}")
        import traceback
        traceback.print_exc()
        
        # 使用 Fallback
        logger.info("[Summary] 使用 Fallback 生成摘要")
        message = generate_fallback_summary(state)
        
        return {"response_message": message}


# ============================================================================
# 測試函數
# ============================================================================

def test_summary_generator():
    """
    測試摘要生成
    """
    print("=" * 60)
    print("Summary Generator 測試")
    print("=" * 60)
    
    test_cases = [
        # 案例 1: 正常記帳
        {
            "amount": 150.0,
            "transaction_type": "expense",
            "description": "午餐",
            "category_name": "食物飲料",
            "merchant": "便當店",
            "is_anomaly": False,
            "budget_level": "normal",
            "budget_usage_pct": 65.0,
            "budget_remaining": 1050.0,
            "db_success": True
        },
        
        # 案例 2: 異常交易 + 預算警告
        {
            "amount": 2500.0,
            "transaction_type": "expense",
            "description": "高檔餐廳晚餐",
            "category_name": "食物飲料",
            "merchant": "高級餐廳",
            "is_anomaly": True,
            "anomaly_reason": "金額異常偏高",
            "anomaly_severity": "high",
            "budget_level": "critical",
            "budget_usage_pct": 95.0,
            "budget_remaining": 150.0,
            "db_success": True
        },
        
        # 案例 3: 預算超支
        {
            "amount": 1000.0,
            "transaction_type": "expense",
            "description": "購物",
            "category_name": "購物消費",
            "merchant": "商場",
            "is_anomaly": False,
            "budget_level": "exceeded",
            "budget_usage_pct": 110.0,
            "budget_remaining": -300.0,
            "db_success": True
        },
        
        # 案例 4: 收入
        {
            "amount": 35000.0,
            "transaction_type": "income",
            "description": "薪水",
            "category_name": "薪資收入",
            "merchant": None,
            "is_anomaly": False,
            "budget_level": "income",
            "db_success": True
        },
        
        # 案例 5: 錯誤情況
        {
            "error": "無法識別金額",
            "db_success": False
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n【測試案例 {i}】")
        print(f"輸入: {test_case.get('description', '錯誤')}")
        
        result = summary_generator_node(test_case)
        
        print(f"\n回覆訊息:")
        print("-" * 60)
        print(result.get("response_message"))
        print("-" * 60)


if __name__ == "__main__":
    # 設定 logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # 執行測試
    test_summary_generator()