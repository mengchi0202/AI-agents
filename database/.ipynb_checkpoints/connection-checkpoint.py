import os
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

# 載入 .env
load_dotenv()

def get_db_connection():
    """建立資料庫連線"""
    try:
        conn = psycopg2.connect(
            host=os.getenv("DB_HOST", "127.0.0.1"),
            port=os.getenv("DB_PORT", "5432"),
            database=os.getenv("DB_NAME", "pfm_agents"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD")
        )
        return conn
    except Exception as e:
        print(f"❌ 資料庫連線失敗: {e}")
        return None

def execute_query(sql, params=None, fetch=True):
    """執行 SQL 並回傳結果 (字典格式)"""
    conn = get_db_connection()
    if not conn:
        return None
    
    result = None
    try:
        # 使用 RealDictCursor 讓資料變成 {'name': '京都旅遊'} 格式
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(sql, params)
            if fetch:
                result = cur.fetchall()
            conn.commit()
    except Exception as e:
        print(f"❌ SQL 執行出錯: {e}")
        conn.rollback()
    finally:
        conn.close()
    return result