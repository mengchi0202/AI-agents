from datetime import datetime, date

def calculate_goal_metrics(target_amount: float, current_amount: float, deadline: str):
    today = date.today()
    target_date = datetime.strptime(deadline, "%Y-%m-%d").date()
    days_left = max((target_date - today).days, 1)
    
    completion_rate = round((current_amount / target_amount) * 100, 1)
    gap = max(target_amount - current_amount, 0)
    daily_needed = round(gap / days_left, 0)
    
    return {
        "completion_rate": completion_rate,
        "days_left": days_left,
        "gap": gap,
        "daily_needed": daily_needed
    }

def judge_lagging_status(metrics: dict, start_date: str):
    start = datetime.strptime(start_date, "%Y-%m-%d").date()
    total_days = max(metrics['days_left'] + (date.today() - start).days, 1)
    elapsed_days = (date.today() - start).days
    
    # 理想進度
    expected_rate = (elapsed_days / total_days) * 100
    expected_rate = min(max(expected_rate, 0), 100) # 確保在 0~100 之間
    
    # 判斷是否落後 20%
    is_lagging = (expected_rate - metrics['completion_rate']) > 20
    
    return is_lagging, expected_rate
