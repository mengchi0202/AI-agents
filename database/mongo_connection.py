"""
MongoDB 連線管理
用於儲存彈性數據：對話狀態、LLM 日誌、使用者行為等
"""

import os
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

# MongoDB 設定
MONGO_CONFIG = {
    "host": os.getenv("MONGO_HOST", "localhost"),
    "port": int(os.getenv("MONGO_PORT", "27017")),
    "db_name": os.getenv("MONGO_DB", "pfm_agents"),
}

# 全域連線（避免重複建立）
_client = None
_db = None


def get_mongo_db():
    """取得 MongoDB 資料庫物件"""
    global _client, _db
    if _db is None:
        _client = MongoClient(MONGO_CONFIG["host"], MONGO_CONFIG["port"])
        _db = _client[MONGO_CONFIG["db_name"]]
    return _db


def close_mongo():
    """關閉 MongoDB 連線"""
    global _client, _db
    if _client:
        _client.close()
        _client = None
        _db = None


# 測試連線
if __name__ == "__main__":
    try:
        db = get_mongo_db()
        # ping 測試
        db.command("ping")
        print(f"✅ MongoDB 連線成功: {MONGO_CONFIG['db_name']}")
        print(f"   Collections: {db.list_collection_names()}")
        close_mongo()
    except Exception as e:
        print(f"❌ MongoDB 連線失敗: {e}")