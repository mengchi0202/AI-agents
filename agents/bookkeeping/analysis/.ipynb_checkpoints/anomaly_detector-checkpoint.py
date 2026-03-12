#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Anomaly Detector Node - LangGraph 版本（LLM + 統計規則混合）
1. 統計規則：查歷史數據算平均和標準差
2. LLM 判斷：把統計結果 + 交易資訊丟給 TAIDE 綜合判斷
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
    from ....database.crud import get_category_statistics
except (ImportError, ValueError):
    try:
        # 嘗試絕對導入
        from src.models import get_taide_model
        from src.database.crud import get_category_statistics
    except ImportError:
        logger.warning("無法導入模組，使用 Mock 函數")
        
        # Mock 函數
        def get_taide_model():
            class MockModel:
                is_loaded = True
                def load(self): pass
                def generate(self, prompt, **kwargs):
                    return '{"is_anomaly": false, "severity": "none", "reason": "金額正常", "suggestion": null}'
            return MockModel()
        
        def get_category_statistics(user_id: int, category: str):
            return None  # 使用內建 Mock 數據


# ============================================================================
# Mock 歷史數據（Fallback，當資料庫無數據時使用）
# ============================================================================

MOCK_HISTORY = {
    "食物飲料": {"avg": 120, "std": 40, "max": 250, "count": 30},
    "午餐": {"avg": 120, "std": 40, "max": 250, "count": 30},
    "晚餐": {"avg": 200, "std": 60, "max": 450, "count": 25},
    "早餐": {"avg": 65, "std": 20, "max": 120, "count": 20},
    "飲料": {"avg": 55, "std": 15, "max": 100, "count": 40},
    "交通運輸": {"avg": 80, "std": 30, "max": 200, "count": 15},
    "購物消費": {"avg": 500, "std": 300, "max": 2000, "count": 10},
    "娛樂休閒": {"avg": 350, "std": 150, "max": 800, "count": 8},
    "醫療保健": {"avg": 300, "std": 200, "max": 1000, "count": 5},
    "教育學習": {"avg": 400, "std": 250, "max": 1200, "count": 6},
    "居住水電": {"avg": 800, "std": 200, "max": 1500, "count": 12},
    "其他支出": {"avg": 200, "std": 150, "max": 800, "count": 20},
}


def get_category_stats(category_name: str, user_id: int = None) -> Optional[Dict]:
    """
    取得該分類的歷史統計資料
    
    優先順序：
    1. 從資料庫查詢用戶的歷史數據
    2. 使用 Mock 數據（開發/測試用）
    3. 返回 None（無歷史數據）
    """
    # 嘗試從資料庫查詢
    if user_id:
        try:
            db_stats = get_category_statistics(user_id, category_name)
            if db_stats:
                logger.info(f"[Anomaly] 使用資料庫統計數據: {category_name}")
                return db_stats
        except Exception as e:
            logger.warning(f"[Anomaly] 查詢資料庫失敗: {e}")
    
    # 嘗試精確匹配 Mock 數據
    if category_name in MOCK_HISTORY:
        logger.info(f"[Anomaly] 使用 Mock 統計數據: {category_name}")
        return MOCK_HISTORY[category_name]
    
    # 嘗試模糊匹配
    for key, stats in MOCK_HISTORY.items():
        if key in category_name or category_name in key:
            logger.info(f"[Anomaly] 使用模糊匹配 Mock 數據: {key} → {category_name}")
            return stats
    
    # 沒有歷史資料
    logger.warning(f"[Anomaly] 無歷史數據: {category_name}")
    return None


# ============================================================================
# 統計規則判斷
# ============================================================================

def stat_check(amount: float, stats: Dict) -> Dict:
    """
    用統計規則初步判斷是否異常
    
    規則：
    - 超過 平均 + 2倍標準差 → medium（可能異常）
    - 超過 平均 + 3倍標準差 → high（高度異常）
    - 超過歷史最大值 → high（超過歷史記錄）
    
    返回：
    {
        "stat_flag": "normal" | "medium" | "high",
        "reason": "原因說明",
        "avg": 平均值,
        "std": 標準差,
        "deviation": 偏離標準差的倍數
    }
    """
    avg = stats["avg"]
    std = stats["std"]
    historical_max = stats["max"]
    
    threshold_2std = avg + 2 * std
    threshold_3std = avg + 3 * std
    
    # 計算偏離程度（幾個標準差）
    deviation = round((amount - avg) / std, 1) if std > 0 else 0
    
    if amount > historical_max:
        return {
            "stat_flag": "high",
            "reason": f"超過歷史最高 ${historical_max:.0f}",
            "avg": avg,
            "std": std,
            "deviation": deviation,
        }
    elif amount > threshold_3std:
        return {
            "stat_flag": "high",
            "reason": f"超過平均值 3 倍標準差（平均 ${avg:.0f}）",
            "avg": avg,
            "std": std,
            "deviation": deviation,
        }
    elif amount > threshold_2std:
        return {
            "stat_flag": "medium",
            "reason": f"超過平均值 2 倍標準差（平均 ${avg:.0f}）",
            "avg": avg,
            "std": std,
            "deviation": deviation,
        }
    else:
        return {
            "stat_flag": "normal",
            "reason": "在正常範圍內",
            "avg": avg,
            "std": std,
            "deviation": deviation,
        }


# ============================================================================
# LLM Prompt
# ============================================================================

ANOMALY_PROMPT = """你是一個專業的財務異常偵測助手。根據以下交易資訊和歷史統計數據，判斷這筆交易是否異常。

交易資訊：
- 描述：{description}
- 金額：${amount}
- 分類：{category}
- 商家：{merchant}

歷史統計（同分類）：
- 平均消費：${avg:.0f}
- 標準差：${std:.0f}
- 歷史最高：${max:.0f}
- 交易次數：{count}
- 統計判斷：{stat_flag}（{stat_reason}）
- 偏離程度：{deviation} 個標準差

請綜合判斷這筆交易是否異常。考慮：
1. 金額是否明顯偏離歷史平均
2. 該消費在該分類下是否合理
3. 是否可能是特殊情況（如聚餐、節日、一次性消費、大額採購）

請以 JSON 格式回答，只回覆 JSON，不要其他文字：
{{
    "is_anomaly": true 或 false,
    "severity": "none" 或 "low" 或 "medium" 或 "high",
    "reason": "簡短說明原因（20字以內）",
    "suggestion": "給用戶的建議（20字以內，如果正常則為 null）"
}}

範例：
輸入：午餐花費 $800（平均 $120）
輸出：{{"is_anomaly": true, "severity": "high", "reason": "午餐金額異常偏高", "suggestion": "確認是否為聚餐或特殊消費"}}
"""

ANOMALY_PROMPT_NO_HISTORY = """你是一個專業的財務異常偵測助手。這筆交易沒有歷史數據可以比對，請根據常識和經驗判斷是否異常。

交易資訊：
- 描述：{description}
- 金額：${amount}
- 分類：{category}
- 商家：{merchant}

請以 JSON 格式回答，只回覆 JSON：
{{
    "is_anomaly": true 或 false,
    "severity": "none" 或 "low" 或 "medium" 或 "high",
    "reason": "簡短說明原因（20字以內）",
    "suggestion": "給用戶的建議（20字以內，如果正常則為 null）"
}}

範例：
輸入：早餐 $5000
輸出：{{"is_anomaly": true, "severity": "high", "reason": "早餐金額明顯過高", "suggestion": "請確認金額是否正確"}}
"""


# ============================================================================
# LLM 回應解析
# ============================================================================

def parse_llm_response(response: str) -> Dict:
    """
    解析 LLM 回應的 JSON
    
    處理各種可能的格式：
    1. 純 JSON
    2. Markdown code block
    3. 包含額外文字
    """
    try:
        text = response.strip()
        
        # 移除可能的 markdown 標記
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0]
        elif "```" in text:
            text = text.split("```")[1].split("```")[0]
        
        text = text.strip()
        
        # 提取 JSON 部分
        start = text.find("{")
        end = text.rfind("}") + 1
        if start != -1 and end > start:
            text = text[start:end]
        
        result = json.loads(text)
        
        return {
            "is_anomaly": bool(result.get("is_anomaly", False)),
            "severity": result.get("severity", "none"),
            "reason": result.get("reason", ""),
            "suggestion": result.get("suggestion"),
        }
    
    except Exception as e:
        logger.warning(f"[Anomaly] LLM 回應解析失敗: {e}")
        logger.warning(f"[Anomaly] 原始回應: {response[:200]}")
        
        return {
            "is_anomaly": False,
            "severity": "none",
            "reason": "無法判斷",
            "suggestion": None,
        }


# ============================================================================
# 規則判斷（Fallback）
# ============================================================================

def rule_based_anomaly_check(amount: float, category: str, description: str) -> Dict:
    """
    基於規則的異常檢測（當 LLM 不可用時的 fallback）
    
    簡單規則：
    - 食物類超過 $500 → 異常
    - 交通類超過 $500 → 異常
    - 購物類超過 $5000 → 異常
    - 任何類別超過 $10000 → 高度異常
    """
    # 極端金額檢查
    if amount > 10000:
        return {
            "is_anomaly": True,
            "severity": "high",
            "reason": "金額異常高",
            "suggestion": "請確認金額是否正確"
        }
    
    # 分類特定規則
    category_lower = category.lower()
    
    if "食物" in category_lower or "飲料" in category_lower:
        if amount > 500:
            return {
                "is_anomaly": True,
                "severity": "medium",
                "reason": "餐飲金額偏高",
                "suggestion": "確認是否為聚餐"
            }
    
    elif "交通" in category_lower:
        if amount > 500:
            return {
                "is_anomaly": True,
                "severity": "medium",
                "reason": "交通費用偏高",
                "suggestion": "確認交通方式"
            }
    
    elif "購物" in category_lower:
        if amount > 5000:
            return {
                "is_anomaly": True,
                "severity": "high",
                "reason": "購物金額很高",
                "suggestion": "注意消費控制"
            }
    
    # 正常
    return {
        "is_anomaly": False,
        "severity": "none",
        "reason": "金額正常",
        "suggestion": None
    }


# ============================================================================
# LangGraph Node
# ============================================================================

def anomaly_detector_node(state: dict) -> dict:
    """
    Anomaly Detector Node（LLM + 統計規則混合）
    
    流程：
    1. 查詢歷史統計數據
    2. 使用統計規則初步判斷
    3. 調用 LLM 綜合判斷
    4. 返回異常檢測結果
    
    輸入: amount, category_name, description, merchant, user_id
    輸出: is_anomaly, anomaly_reason, anomaly_severity, anomaly_suggestion
    """
    # 如果前面的 node 有錯誤，跳過
    if state.get("error"):
        logger.warning("[Anomaly] ⚠️ 偵測到錯誤，跳過異常檢測")
        return {}
    
    amount = state.get("amount", 0)
    category = state.get("category_name", "其他支出")
    description = state.get("description", "")
    merchant = state.get("merchant", "未知")
    user_id = state.get("user_id")
    
    logger.info(f"[Anomaly] 開始異常檢測")
    logger.info(f"  金額: ${amount}")
    logger.info(f"  分類: {category}")
    logger.info(f"  描述: {description}")
    
    # 金額驗證
    if amount <= 0:
        logger.warning("[Anomaly] ⚠️ 金額無效，跳過異常檢測")
        return {
            "is_anomaly": False,
            "anomaly_reason": "金額無效，跳過異常偵測",
            "anomaly_method": "skipped"
        }
    
    try:
        # ====================================
        # Step 1: 查歷史統計
        # ====================================
        stats = get_category_stats(category, user_id)
        
        # ====================================
        # Step 2: 統計規則初步判斷
        # ====================================
        stat_result = None
        if stats:
            stat_result = stat_check(amount, stats)
            logger.info(f"[Anomaly] 統計判斷: {stat_result['stat_flag']} ({stat_result['reason']})")
        
        # ====================================
        # Step 3: LLM 綜合判斷
        # ====================================
        try:
            # 取得模型
            model = get_taide_model()
            if not model.is_loaded:
                model.load()
            
            # 組合 prompt
            if stats and stat_result:
                prompt = ANOMALY_PROMPT.format(
                    description=description,
                    amount=amount,
                    category=category,
                    merchant=merchant or "未知",
                    avg=stats["avg"],
                    std=stats["std"],
                    max=stats["max"],
                    count=stats["count"],
                    stat_flag=stat_result["stat_flag"],
                    stat_reason=stat_result["reason"],
                    deviation=stat_result["deviation"],
                )
                method = "llm+stats"
            else:
                prompt = ANOMALY_PROMPT_NO_HISTORY.format(
                    description=description,
                    amount=amount,
                    category=category,
                    merchant=merchant or "未知",
                )
                method = "llm_only"
            
            # 調用 LLM
            logger.info("[Anomaly] 呼叫 TAIDE 模型...")
            response = model.generate(prompt, temperature=0.1, max_new_tokens=256)
            logger.info(f"[Anomaly] LLM 回應: {response}")
            
            # 解析回應
            llm_result = parse_llm_response(response)
        
        except Exception as e:
            logger.warning(f"[Anomaly] LLM 判斷失敗，使用規則判斷: {e}")
            
            # Fallback 到規則判斷
            llm_result = rule_based_anomaly_check(amount, category, description)
            method = "rules_only"
        
        # ====================================
        # Step 4: 返回結果
        # ====================================
        logger.info(f"[Anomaly] {'⚠️ 異常' if llm_result['is_anomaly'] else '✅ 正常'}")
        logger.info(f"  嚴重度: {llm_result['severity']}")
        logger.info(f"  原因: {llm_result['reason']}")
        if llm_result['suggestion']:
            logger.info(f"  建議: {llm_result['suggestion']}")
        
        return {
            "is_anomaly": llm_result["is_anomaly"],
            "anomaly_reason": llm_result["reason"],
            "anomaly_severity": llm_result["severity"],
            "anomaly_suggestion": llm_result["suggestion"],
            "anomaly_stat_flag": stat_result["stat_flag"] if stat_result else "unknown",
            "anomaly_method": method,
        }
    
    except Exception as e:
        logger.error(f"[Anomaly] ❌ 異常檢測失敗: {e}")
        import traceback
        traceback.print_exc()
        
        return {
            "is_anomaly": False,
            "anomaly_reason": f"異常偵測失敗: {str(e)}",
            "anomaly_method": "error",
        }


# ============================================================================
# 測試函數
# ============================================================================

def test_anomaly_detector():
    """
    測試異常檢測器
    """
    print("=" * 60)
    print("Anomaly Detector 測試")
    print("=" * 60)
    
    test_cases = [
        {
            "description": "麥當勞午餐",
            "amount": 159.0,
            "category_name": "食物飲料",
            "merchant": "McDonald's",
            "user_id": 1
        },
        {
            "description": "高檔餐廳晚餐",
            "amount": 2500.0,
            "category_name": "食物飲料",
            "merchant": "高級餐廳",
            "user_id": 1
        },
        {
            "description": "買筆電",
            "amount": 35000.0,
            "category_name": "購物消費",
            "merchant": "Apple Store",
            "user_id": 1
        },
        {
            "description": "捷運卡加值",
            "amount": 500.0,
            "category_name": "交通運輸",
            "merchant": None,
            "user_id": 1
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n【測試案例 {i}】")
        print(f"輸入: {test_case}")
        
        result = anomaly_detector_node(test_case)
        
        print(f"輸出:")
        print(f"  是否異常: {result.get('is_anomaly')}")
        print(f"  嚴重度: {result.get('anomaly_severity')}")
        print(f"  原因: {result.get('anomaly_reason')}")
        print(f"  建議: {result.get('anomaly_suggestion')}")
        print(f"  方法: {result.get('anomaly_method')}")
        print("-" * 60)


if __name__ == "__main__":
    # 設定 logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # 執行測試
    test_anomaly_detector()