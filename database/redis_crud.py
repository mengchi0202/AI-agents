"""
Redis 快取操作
用於：使用者 Session、預算快取、分類快取、Rate Limiting
"""

import json
from .redis_connection import get_redis


# ==========================================
# 1. 使用者 Session（對話暫存）
# ==========================================

def set_session(user_id, data, expire_seconds=1800):
    """設定使用者 Session（預設 30 分鐘過期）"""
    r = get_redis()
    key = f"session:{user_id}"
    r.setex(key, expire_seconds, json.dumps(data, ensure_ascii=False))
    return True


def get_session(user_id):
    """取得使用者 Session"""
    r = get_redis()
    key = f"session:{user_id}"
    data = r.get(key)
    return json.loads(data) if data else None


def delete_session(user_id):
    """刪除使用者 Session"""
    r = get_redis()
    return r.delete(f"session:{user_id}")


# ==========================================
# 2. 預算快取
# ==========================================

def cache_budget(user_id, budget_data, expire_seconds=3600):
    """快取使用者預算（預設 1 小時過期）"""
    r = get_redis()
    key = f"budget:{user_id}"
    r.setex(key, expire_seconds, json.dumps(budget_data, ensure_ascii=False))
    return True


def get_cached_budget(user_id):
    """取得快取的預算"""
    r = get_redis()
    data = r.get(f"budget:{user_id}")
    return json.loads(data) if data else None


def invalidate_budget(user_id):
    """清除預算快取（當有新交易時呼叫）"""
    r = get_redis()
    return r.delete(f"budget:{user_id}")


# ==========================================
# 3. 分類快取
# ==========================================

def cache_categories(categories, expire_seconds=86400):
    """快取所有分類（預設 24 小時過期）"""
    r = get_redis()
    r.setex("categories:all", expire_seconds, json.dumps(categories, ensure_ascii=False))
    return True


def get_cached_categories():
    """取得快取的分類"""
    r = get_redis()
    data = r.get("categories:all")
    return json.loads(data) if data else None


# ==========================================
# 4. Rate Limiting（API 限流）
# ==========================================

def check_rate_limit(user_id, max_requests=30, window_seconds=60):
    """
    檢查是否超過請求限制
    預設：每分鐘最多 30 次
    回傳: (是否允許, 剩餘次數)
    """
    r = get_redis()
    key = f"rate:{user_id}"
    current = r.get(key)

    if current is None:
        r.setex(key, window_seconds, 1)
        return True, max_requests - 1

    count = int(current)
    if count >= max_requests:
        return False, 0

    r.incr(key)
    return True, max_requests - count - 1


# ==========================================
# 5. 即時統計快取
# ==========================================

def cache_daily_total(user_id, date_str, total, expire_seconds=7200):
    """快取當日消費總額（預設 2 小時過期）"""
    r = get_redis()
    key = f"daily_total:{user_id}:{date_str}"
    r.setex(key, expire_seconds, str(total))
    return True


def get_cached_daily_total(user_id, date_str):
    """取得快取的當日消費總額"""
    r = get_redis()
    data = r.get(f"daily_total:{user_id}:{date_str}")
    return float(data) if data else None


def increment_daily_total(user_id, date_str, amount):
    """增加當日消費總額（記帳時呼叫）"""
    r = get_redis()
    key = f"daily_total:{user_id}:{date_str}"
    if r.exists(key):
        r.incrbyfloat(key, amount)
    else:
        r.setex(key, 7200, str(amount))
    return True