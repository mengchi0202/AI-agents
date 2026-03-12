import uuid
import datetime as dt  # 給模組一個別名 dt
MOCK_CATEGORIES = [
    {"category_id": 1, "name": "食物飲料"},
    {"category_id": 2, "name": "交通運輸"},
]

def get_all_categories(): 
    return MOCK_CATEGORIES

def get_category_by_name(name): 
    return {"category_id": 1, "name": "食物飲料"}

def get_category_statistics(user_id, category): 
    return {"avg": 120, "std": 40, "max": 250, "min": 50, "count": 30}

def get_user_budget(user_id, category): 
    return {"amount": 3000}

def get_category_spending(user_id, category): 
    return 2000.0

def create_transaction(data): 
    return {"transaction_id": str(uuid.uuid4()), **data, "created_at": datetime.now().isoformat()}

def get_user_by_id(user_id): 
    return {"user_id": user_id, "name": "測試用戶"}
"""
CRUD 操作 - 資料庫的新增、查詢、更新、刪除
"""

from datetime import date, datetime
from .connection import execute_query


# ==========================================
# Users 使用者
# ==========================================

def create_user(line_user_id, display_name=None, birthday=None, age=None, gender=None):
    """新增使用者"""
    sql = """
        INSERT INTO users (line_user_id, display_name, birthday, age, gender)
        VALUES (%s, %s, %s, %s, %s)
        RETURNING *;
    """
    result = execute_query(sql, (line_user_id, display_name, birthday, age, gender), fetch=True)
    return result[0] if result else None


def get_user_by_line_id(line_user_id):
    """用 LINE ID 查詢使用者"""
    sql = "SELECT * FROM users WHERE line_user_id = %s;"
    result = execute_query(sql, (line_user_id,), fetch=True)
    return result[0] if result else None


# ==========================================
# Transactions 交易記錄
# ==========================================

def create_transaction(user_id, transaction_type, amount, category_id=None,
                       description=None, merchant=None, transaction_date=None):
    """新增交易記錄"""
    if transaction_date is None:
        transaction_date = date.today()

    sql = """
        INSERT INTO transactions 
            (user_id, transaction_type, amount, category_id, description, merchant, transaction_date)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        RETURNING *;
    """
    result = execute_query(
        sql,
        (user_id, transaction_type, amount, category_id, description, merchant, transaction_date),
        fetch=True
    )
    return result[0] if result else None


def get_transactions(user_id, start_date=None, end_date=None, category_id=None, limit=50):
    """查詢交易記錄"""
    sql = "SELECT * FROM transactions WHERE user_id = %s"
    params = [user_id]

    if start_date:
        sql += " AND transaction_date >= %s"
        params.append(start_date)
    if end_date:
        sql += " AND transaction_date <= %s"
        params.append(end_date)
    if category_id:
        sql += " AND category_id = %s"
        params.append(category_id)

    sql += " ORDER BY transaction_date DESC LIMIT %s;"
    params.append(limit)

    return execute_query(sql, tuple(params), fetch=True)


def get_monthly_summary(user_id, year, month):
    """取得月度摘要"""
    sql = """
        SELECT 
            transaction_type,
            COALESCE(c.name, '未分類') as category_name,
            COUNT(*) as count,
            SUM(t.amount) as total
        FROM transactions t
        LEFT JOIN categories c ON t.category_id = c.category_id
        WHERE t.user_id = %s
          AND EXTRACT(YEAR FROM t.transaction_date) = %s
          AND EXTRACT(MONTH FROM t.transaction_date) = %s
        GROUP BY transaction_type, c.name
        ORDER BY transaction_type, total DESC;
    """
    return execute_query(sql, (user_id, year, month), fetch=True)


# ==========================================
# Categories 分類
# ==========================================

def get_all_categories():
    """取得所有分類"""
    sql = "SELECT * FROM categories ORDER BY category_id;"
    return execute_query(sql, fetch=True)


def get_category_by_name(name):
    """用名稱查詢分類"""
    sql = "SELECT * FROM categories WHERE name = %s;"
    result = execute_query(sql, (name,), fetch=True)
    return result[0] if result else None


# ==========================================
# Budgets 預算
# ==========================================

def create_budget(user_id, category_id, amount, period='monthly',
                  start_date=None, end_date=None):
    """新增預算"""
    if start_date is None:
        today = date.today()
        start_date = today.replace(day=1)
    if end_date is None:
        # 預設到月底
        if start_date.month == 12:
            end_date = start_date.replace(year=start_date.year + 1, month=1, day=1)
        else:
            end_date = start_date.replace(month=start_date.month + 1, day=1)

    sql = """
        INSERT INTO budgets (user_id, category_id, amount, period, start_date, end_date)
        VALUES (%s, %s, %s, %s, %s, %s)
        RETURNING *;
    """
    result = execute_query(
        sql,
        (user_id, category_id, amount, period, start_date, end_date),
        fetch=True
    )
    return result[0] if result else None


def get_budgets(user_id):
    """查詢使用者的預算"""
    sql = """
        SELECT b.*, c.name as category_name
        FROM budgets b
        LEFT JOIN categories c ON b.category_id = c.category_id
        WHERE b.user_id = %s
        ORDER BY b.start_date DESC;
    """
    return execute_query(sql, (user_id,), fetch=True)


# ==========================================
# Financial Goals 財務目標
# ==========================================

def create_goal(user_id, name, target_amount, deadline=None):
    """新增財務目標"""
    sql = """
        INSERT INTO financial_goals (user_id, name, target_amount, deadline)
        VALUES (%s, %s, %s, %s)
        RETURNING *;
    """
    result = execute_query(sql, (user_id, name, target_amount, deadline), fetch=True)
    return result[0] if result else None


def get_goals(user_id):
    """查詢財務目標 - 確保 user_id 正確傳入並按時間排序"""
    # 確保傳入的是字串，避免 UUID 或其他型別導致資料庫報錯
    user_id_str = str(user_id)
    
    # 這裡的 SQL 與你的資料表結構完全吻合
    sql = "SELECT * FROM financial_goals WHERE user_id = %s ORDER BY created_at DESC;"
    
    try:
        results = execute_query(sql, (user_id_str,), fetch=True)
        # 如果沒抓到資料，回傳空陣列而不是 None，避免後續跑迴圈時當掉
        return results if results else []
    except Exception as e:
        print(f"❌ get_goals 執行出錯: {e}")
        return []
def update_goal_amount(goal_id, current_amount):
    """更新目標進度"""
    sql = """
        UPDATE financial_goals 
        SET current_amount = %s
        WHERE goal_id = %s
        RETURNING *;
    """
    result = execute_query(sql, (current_amount, goal_id), fetch=True)
    return result[0] if result else None