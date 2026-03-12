"""
MongoDB CRUD 操作
儲存彈性數據：對話狀態、LLM 日誌、使用者行為、事件、財經新聞、目標策略
"""

from datetime import datetime
from .mongo_connection import get_mongo_db


# ==========================================
# 1. Agent 對話狀態
# ==========================================

def save_conversation_state(user_id, session_id, state_data):
    """儲存 Agent 對話狀態"""
    db = get_mongo_db()
    doc = {
        "user_id": user_id,
        "session_id": session_id,
        "state": state_data,
        "updated_at": datetime.now(),
    }
    result = db.conversation_states.update_one(
        {"user_id": user_id, "session_id": session_id},
        {"$set": doc},
        upsert=True
    )
    return str(result.upserted_id) if result.upserted_id else "updated"


def get_conversation_state(user_id, session_id):
    """取得對話狀態"""
    db = get_mongo_db()
    return db.conversation_states.find_one(
        {"user_id": user_id, "session_id": session_id},
        {"_id": 0}
    )


# ==========================================
# 2. LLM 解析日誌
# ==========================================

def save_llm_log(user_id, agent_name, input_text, output_text, model_name="TAIDE-LX-7B", latency_ms=None):
    """儲存 LLM 呼叫日誌"""
    db = get_mongo_db()
    doc = {
        "user_id": user_id,
        "agent_name": agent_name,
        "model": model_name,
        "input": input_text,
        "output": output_text,
        "latency_ms": latency_ms,
        "created_at": datetime.now(),
    }
    result = db.llm_logs.insert_one(doc)
    return str(result.inserted_id)


def get_llm_logs(user_id=None, agent_name=None, limit=20):
    """查詢 LLM 日誌"""
    db = get_mongo_db()
    query = {}
    if user_id:
        query["user_id"] = user_id
    if agent_name:
        query["agent_name"] = agent_name
    return list(db.llm_logs.find(query, {"_id": 0}).sort("created_at", -1).limit(limit))


# ==========================================
# 3. 事件總線（Agent 間通訊記錄）
# ==========================================

def save_event(event_type, source_agent, target_agent, payload):
    """儲存事件"""
    db = get_mongo_db()
    doc = {
        "event_type": event_type,
        "source": source_agent,
        "target": target_agent,
        "payload": payload,
        "status": "pending",
        "created_at": datetime.now(),
    }
    result = db.events.insert_one(doc)
    return str(result.inserted_id)


def get_events(event_type=None, status=None, limit=50):
    """查詢事件"""
    db = get_mongo_db()
    query = {}
    if event_type:
        query["event_type"] = event_type
    if status:
        query["status"] = status
    return list(db.events.find(query, {"_id": 0}).sort("created_at", -1).limit(limit))


# ==========================================
# 4. 財經新聞
# ==========================================

def save_news(title, source, content, tags=None, url=None):
    """儲存財經新聞"""
    db = get_mongo_db()
    doc = {
        "title": title,
        "source": source,
        "content": content,
        "tags": tags or [],
        "url": url,
        "created_at": datetime.now(),
    }
    result = db.financial_news.insert_one(doc)
    return str(result.inserted_id)


def get_news(tags=None, limit=10):
    """查詢財經新聞"""
    db = get_mongo_db()
    query = {}
    if tags:
        query["tags"] = {"$in": tags}
    return list(db.financial_news.find(query, {"_id": 0}).sort("created_at", -1).limit(limit))


# ==========================================
# 5. 使用者行為
# ==========================================

def save_user_behavior(user_id, action, details=None):
    """記錄使用者行為"""
    db = get_mongo_db()
    doc = {
        "user_id": user_id,
        "action": action,
        "details": details or {},
        "created_at": datetime.now(),
    }
    result = db.user_behaviors.insert_one(doc)
    return str(result.inserted_id)


def get_user_behaviors(user_id, action=None, limit=50):
    """查詢使用者行為"""
    db = get_mongo_db()
    query = {"user_id": user_id}
    if action:
        query["action"] = action
    return list(db.user_behaviors.find(query, {"_id": 0}).sort("created_at", -1).limit(limit))


# ==========================================
# 6. 目標策略建議
# ==========================================

def save_strategy(user_id, goal_name, strategy_type, recommendations):
    """儲存 AI 產生的目標策略建議"""
    db = get_mongo_db()
    doc = {
        "user_id": user_id,
        "goal_name": goal_name,
        "strategy_type": strategy_type,
        "recommendations": recommendations,
        "created_at": datetime.now(),
    }
    result = db.goal_strategies.insert_one(doc)
    return str(result.inserted_id)


def get_strategies(user_id, goal_name=None, limit=10):
    """查詢目標策略"""
    db = get_mongo_db()
    query = {"user_id": user_id}
    if goal_name:
        query["goal_name"] = goal_name
    return list(db.goal_strategies.find(query, {"_id": 0}).sort("created_at", -1).limit(limit))