"""
Redis 連線管理
用於快取、Session、即時數據
"""

import os
import redis
from dotenv import load_dotenv

load_dotenv()

REDIS_CONFIG = {
    "host": os.getenv("REDIS_HOST", "localhost"),
    "port": int(os.getenv("REDIS_PORT", "6379")),
    "db": int(os.getenv("REDIS_DB", "0")),
    "decode_responses": True,
}

_redis_client = None


def get_redis():
    """取得 Redis 連線"""
    global _redis_client
    if _redis_client is None:
        _redis_client = redis.Redis(**REDIS_CONFIG)
    return _redis_client


def close_redis():
    """關閉 Redis 連線"""
    global _redis_client
    if _redis_client:
        _redis_client.close()
        _redis_client = None


# 測試連線
if __name__ == "__main__":
    try:
        r = get_redis()
        r.ping()
        print(f"✅ Redis 連線成功")
        close_redis()
    except Exception as e:
        print(f"❌ Redis 連線失敗: {e}")