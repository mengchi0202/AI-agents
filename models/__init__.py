#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Models Module
"""

import os
import logging

logger = logging.getLogger(__name__)

# 判斷是否使用真實模型
USE_REAL_MODEL = os.getenv("USE_REAL_MODEL", "false").lower() == "true"

if USE_REAL_MODEL:
    try:
        from .taide_model import get_taide_model
        logger.info("[Models] ✅ 使用真實 TAIDE 模型")
    except Exception as e:
        logger.error(f"[Models] ❌ 無法載入真實模型: {e}")
        USE_REAL_MODEL = False

if not USE_REAL_MODEL:
    logger.info("[Models] 使用 Mock 模型")
    
    class MockTAIDEModel:
        def __init__(self):
            self.is_loaded = True
        
        def load(self):
            self.is_loaded = True
        
        def generate(self, prompt: str, temperature: float = 0.1, max_new_tokens: int = 256) -> str:
            if "解析" in prompt or "交易資訊" in prompt:
                return '{"amount": 159.0, "transaction_type": "expense", "description": "麥當勞", "merchant": "McDonald\'s", "time_hint": "today"}'
            elif "分類" in prompt:
                return '{"category_name": "食物飲料", "sub_category_name": "午餐", "reason": "速食餐廳"}'
            elif "異常" in prompt:
                return '{"is_anomaly": false, "severity": "none", "reason": "金額正常", "suggestion": null}'
            elif "預算" in prompt:
                return '{"budget_warning": null, "budget_level": "normal", "saving_tip": null}'
            elif "記帳結果" in prompt:
                return "✅ 已記錄：麥當勞 $159（食物飲料）"
            else:
                return '{"response": "測試成功"}'
    
    def get_taide_model():
        return MockTAIDEModel()

__all__ = ['get_taide_model']
