# src/agents/goals/goal_manager.py

import datetime as dt  # 💡 使用 dt 作為別名，徹底解決 isinstance 報錯問題
from datetime import timedelta
from src.database.crud import get_goals  # 確保路徑正確
from .utils import calculate_goal_metrics  # 確保 utils 內有此函數

def goal_manager_node(state: dict):
    """
    負責從資料庫抓取用戶目標，並計算達成率與進度狀態。
    """
    user_id = state.get("user_id")
    
    # 1. 從資料庫抓取目標資料
    goals = get_goals(user_id)
    
    if not goals:
        return {
            "error": "找不到目標數據",
            "is_lagging": False,
            "response_message": "目前沒有設定任何理財目標喔！"
        }

    # 取得最新一筆目標 (因為 SQL 有 ORDER BY created_at DESC)
    # 這樣你剛新增的「日本京都旅遊」就會是這一筆
    goal_data = goals[0]
    
    # 2. 處理 Deadline 日期 (修正之前的 TypeError)
    raw_deadline = goal_data.get('deadline')
    
    # 💡 這裡就是修正 isinstance 報錯的關鍵寫法
    if raw_deadline is None:
        # 如果資料庫沒設日期，給予一年後的預設值
        deadline_dt = dt.datetime.now() + timedelta(days=365)
        deadline_str = deadline_dt.strftime("%Y-%m-%d")
    elif isinstance(raw_deadline, (dt.datetime, dt.date)):
        # 成功辨識日期格式，轉為字串供後續計算使用
        deadline_str = raw_deadline.strftime("%Y-%m-%d")
    else:
        # 如果已經是字串，直接使用
        deadline_str = str(raw_deadline)

    # 3. 呼叫工具函數計算進度數據
    # 確保傳入的是 float 類型
    target_amount = float(goal_data.get('target_amount', 0))
    current_amount = float(goal_data.get('current_amount', 0))

    metrics = calculate_goal_metrics(
        target_amount=target_amount,
        current_amount=current_amount,
        deadline=deadline_str
    )
    
    # 4. 回傳更新後的 State
    return {
        "goal_name": goal_data.get("name", "未命名目標"), 
        
        "target_amount": target_amount,
        "current_amount": current_amount,
        "deadline": deadline_str,
        
        # 這些是計算出來的數據，要傳給後面的 Advisor 或 Notifier
        "completion_rate": metrics.get("completion_rate", 0),
        "ideal_progress": metrics.get("ideal_progress", 0),
        "is_lagging": metrics.get("is_lagging", False),
        
        # 確保 state 內也有 metrics 結構，方便測試腳本讀取
        "metrics": metrics 
    }