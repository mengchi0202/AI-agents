"""
建立 pfm_agents 資料表
"""

from .connection import get_connection, close_connection


def create_all_tables():
    """建立所有資料表"""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            # 1. 使用者表
                       # 1. 使用者表
            cur.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id SERIAL PRIMARY KEY,
                    line_user_id VARCHAR(50) UNIQUE NOT NULL,
                    display_name VARCHAR(100),
                    birthday DATE,
                    age INTEGER,
                    gender VARCHAR(10) CHECK (gender IN ('male', 'female', 'other')),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)

            # 2. 分類表
            cur.execute("""
                CREATE TABLE IF NOT EXISTS categories (
                    category_id SERIAL PRIMARY KEY,
                    name VARCHAR(50) NOT NULL,
                    parent_category VARCHAR(50),
                    icon VARCHAR(10),
                    is_default BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)

            # 3. 交易記錄表
            cur.execute("""
                CREATE TABLE IF NOT EXISTS transactions (
                    transaction_id SERIAL PRIMARY KEY,
                    user_id INTEGER REFERENCES users(user_id),
                    transaction_type VARCHAR(20) NOT NULL CHECK (transaction_type IN ('income', 'expense')),
                    amount DECIMAL(12, 2) NOT NULL,
                    category_id INTEGER REFERENCES categories(category_id),
                    description TEXT,
                    merchant VARCHAR(100),
                    transaction_date DATE NOT NULL DEFAULT CURRENT_DATE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)

            # 4. 預算表
            cur.execute("""
                CREATE TABLE IF NOT EXISTS budgets (
                    budget_id SERIAL PRIMARY KEY,
                    user_id INTEGER REFERENCES users(user_id),
                    category_id INTEGER REFERENCES categories(category_id),
                    amount DECIMAL(12, 2) NOT NULL,
                    period VARCHAR(20) DEFAULT 'monthly',
                    start_date DATE NOT NULL,
                    end_date DATE NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)

            # 5. 財務目標表
            cur.execute("""
                CREATE TABLE IF NOT EXISTS financial_goals (
                    goal_id SERIAL PRIMARY KEY,
                    user_id INTEGER REFERENCES users(user_id),
                    name VARCHAR(100) NOT NULL,
                    target_amount DECIMAL(12, 2) NOT NULL,
                    current_amount DECIMAL(12, 2) DEFAULT 0,
                    deadline DATE,
                    status VARCHAR(20) DEFAULT 'active',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)

            # 6. 插入預設分類
            cur.execute("""
                INSERT INTO categories (name, parent_category, icon, is_default)
                SELECT * FROM (VALUES
                    ('飲食', NULL, '🍔', TRUE),
                    ('早餐', '飲食', '🥐', TRUE),
                    ('午餐', '飲食', '🍱', TRUE),
                    ('晚餐', '飲食', '🍽️', TRUE),
                    ('飲料', '飲食', '🧋', TRUE),
                    ('交通', NULL, '🚗', TRUE),
                    ('捷運', '交通', '🚇', TRUE),
                    ('公車', '交通', '🚌', TRUE),
                    ('計程車', '交通', '🚕', TRUE),
                    ('娛樂', NULL, '🎮', TRUE),
                    ('購物', NULL, '🛒', TRUE),
                    ('醫療', NULL, '🏥', TRUE),
                    ('教育', NULL, '📚', TRUE),
                    ('住宿', NULL, '🏠', TRUE),
                    ('薪資', NULL, '💰', TRUE),
                    ('其他收入', NULL, '💵', TRUE),
                    ('其他支出', NULL, '📦', TRUE)
                ) AS v(name, parent_category, icon, is_default)
                WHERE NOT EXISTS (SELECT 1 FROM categories WHERE is_default = TRUE);
            """)

            conn.commit()
            print("✅ 所有資料表建立完成！")

    except Exception as e:
        conn.rollback()
        print(f"❌ 建表失敗: {e}")
        raise
    finally:
        close_connection(conn)


if __name__ == "__main__":
    create_all_tables()