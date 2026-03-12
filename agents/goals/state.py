from typing import TypedDict, Optional, List, Dict, Any

class GoalState(TypedDict):
    user_id: str
    goal_id: str
    goal_name: Optional[str]
    metrics: Dict[str, Any]   
    expected_rate: float
    is_lagging: bool
    advice_options: List[str]
    response_message: str
    db_success: bool
    error: Optional[str]