# src/agents/goals/coordinator.py

from langgraph.graph import StateGraph, END
from .goal_manager import goal_manager_node
from .savings_advisor import savings_advisor_node
from .progress_notifier import progress_notifier_node
# 確保匯入你的 State 定義
from .state import GoalState 

def create_goals_graph():
    # 💡 建議這裡用你定義的 GoalState，不要只用 dict
    workflow = StateGraph(GoalState) 
    
    workflow.add_node("manager", goal_manager_node)
    workflow.add_node("advisor", savings_advisor_node)
    workflow.add_node("notifier", progress_notifier_node)

    workflow.set_entry_point("manager")

    # 路由邏輯：我們強制讓它走 advisor，來測試 AI 生成
    def router(state):
        if state.get("error") or not state.get("goal_name"):
            return "end"
        # 💡 強制走 advisor 節點，這樣不論進度如何 AI 都會說話
        return "advisor"

    # 下面的 add_conditional_edges 也要對齊
    workflow.add_conditional_edges(
        "manager", 
        router, 
        {
            "advisor": "advisor",
            "notifier": "notifier",
            "end": END
        }
    )

    
    
    workflow.add_edge("advisor", "notifier")
    workflow.add_edge("notifier", END)

    return workflow.compile()

goals_app = create_goals_graph()