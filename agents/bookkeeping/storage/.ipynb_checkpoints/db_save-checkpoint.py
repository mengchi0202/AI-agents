#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
DB Save Node - LangGraph 版本
將交易資料儲存到 PostgreSQL
"""

import logging
import uuid
import sys
import os
from datetime import datetime
from typing import Dict, Optional

# 添加專案根目錄到 Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))

logger = logging.getLogger(__name__)


# ============================================================================
# Import 處理
# ============================================================================

try:
    from ....database.crud import create_transaction, get_user_by_id
    from ....database.connection import get_db_cursor
except (ImportError, ValueError):
    try:
        from src.database.crud import create_transaction, get_user_by_id
        from src.database.connection import get_db_cursor
    except ImportError:
        logger.warning("無法導入資料庫模組，使用 Mock")
        
        # Mock 資料庫
        MOCK_DB = []
        
        def create_transaction(transaction_data: dict) -> dict:
            record = {
                "transaction_id": str(uuid.uuid4()),
                **transaction_data,
                "created_at": datetime.now().isoformat(),
            }
            MOCK_DB.append(record)
            return record
        
        def get_user_by_id(user_id: int) -> Optional[dict]:
            return {"user_id": user_id, "name": "測試用戶"}


# ============================================================================
# LangGraph Node
# ============================================================================

def db_save_node(state: dict) -> dict:
    """
    DB Save Node - 儲存交易到資料庫
    
    流程：
    1. 驗證數據完整性
    2. 組合交易數據
    3. 儲存到 PostgreSQL
    4. 返回 transaction_id
    
    輸入: user_id, amount, transaction_type, description, category_id, etc.
    輸出: transaction_id, db_success
    """
    logger.info("[DB Save] 開始儲存交易")
    
    # 如果前面有錯誤，跳過儲存
    if state.get("error"):
        logger.warning("[DB Save] ⚠️ 偵測到錯誤，跳過儲存")
        return {
            "db_success": False,
        }
    
    # 驗證必要欄位
    amount = state.get("amount", 0)
    if amount <= 0:
        logger.error("[DB Save] ❌ 金額無效")
        return {
            "db_success": False,
            "error": "金額無效，無法儲存",
        }
    
    user_id = state.get("user_id")
    if not user_id:
        logger.error("[DB Save] ❌ 缺少 user_id")
        return {
            "db_success": False,
            "error": "缺少用戶 ID",
        }
    
    try:
        # ====================================
        # 組合交易數據
        # ====================================
        transaction_data = {
            "user_id": user_id,
            "amount": amount,
            "transaction_type": state.get("transaction_type", "expense"),
            "description": state.get("description", ""),
            "category_id": state.get("category_id"),
            "category_name": state.get("category_name", "其他支出"),
            "merchant": state.get("merchant"),
            "transaction_date": state.get("transaction_date", datetime.now().date().isoformat()),
            "time_hint": state.get("time_hint"),
            
            # 解析相關
            "parse_confidence": state.get("parse_confidence"),
            "parse_method": state.get("parse_method"),
            
            # 異常檢測相關
            "is_anomaly": state.get("is_anomaly", False),
            "anomaly_reason": state.get("anomaly_reason"),
            "anomaly_severity": state.get("anomaly_severity"),
            "anomaly_suggestion": state.get("anomaly_suggestion"),
            
            # 預算相關
            "budget_warning": state.get("budget_warning"),
            "budget_level": state.get("budget_level"),
        }
        
        logger.info(f"[DB Save] 交易數據:")
        logger.info(f"  金額: ${transaction_data['amount']}")
        logger.info(f"  類型: {transaction_data['transaction_type']}")
        logger.info(f"  描述: {transaction_data['description']}")
        logger.info(f"  分類: {transaction_data['category_name']}")
        logger.info(f"  異常: {transaction_data['is_anomaly']}")
        
        # ====================================
        # 儲存到資料庫
        # ====================================
        record = create_transaction(transaction_data)
        
        transaction_id = record.get("transaction_id")
        
        logger.info(f"[DB Save] ✅ 儲存成功")
        logger.info(f"  交易 ID: {transaction_id}")
        
        return {
            "transaction_id": transaction_id,
            "db_success": True,
        }
    
    except Exception as e:
        logger.error(f"[DB Save] ❌ 儲存失敗: {e}")
        import traceback
        traceback.print_exc()
        
        return {
            "db_success": False,
            "error": f"儲存失敗: {str(e)}",
        }


# ============================================================================
# 測試函數
# ============================================================================

def test_db_save():
    """
    測試資料庫儲存
    """
    print("=" * 60)
    print("DB Save Node 測試")
    print("=" * 60)
    
    test_state = {
        "user_id": 1,
        "amount": 159.0,
        "transaction_type": "expense",
        "description": "麥當勞午餐",
        "category_id": 1,
        "category_name": "食物飲料",
        "merchant": "McDonald's",
        "is_anomaly": False,
        "parse_confidence": 0.95,
        "parse_method": "llm"
    }
    
    print(f"\n輸入: {test_state}\n")
    
    result = db_save_node(test_state)
    
    print(f"\n輸出: {result}\n")
    
    if result.get("db_success"):
        print("✅ 測試通過")
    else:
        print("❌ 測試失敗")
        print(f"錯誤: {result.get('error')}")


if __name__ == "__main__":
    # 設定 logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # 執行測試
    test_db_save()