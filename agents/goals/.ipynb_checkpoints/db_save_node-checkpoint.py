# db_save_node.py
from src.database.crud import update_goal_amount

def goal_db_save_node(state: dict):
    if state.get("error"):
        return state

    # 從 State 取得由 manager 傳遞下來的 goal_id 與最新金額
    goal_id = state.get("goal_id")
    # 假設我們把計算後的 current_amount 存放在 metrics 裡
    current_amount = state.get("metrics", {}).get("current_amount") 

    if goal_id and current_amount:
        # 呼叫你的 CRUD 函數：update_goal_amount(goal_id, current_amount)
        update_goal_amount(goal_id, current_amount)
        return {"db_success": True}
    
    return {"db_success": False}