"""
Bookkeeping LangGraph - 記帳 Domain 完整流程
串接所有 Node：parser → classifier → anomaly → budget → db_save → summary
"""
import logging
from typing import TypedDict, Optional

from langgraph.graph import StateGraph, END

from .processing.transaction_parser import transaction_parser_node
from .classification.category_classifier import category_classifier_node
from .analysis.anomaly_detector import anomaly_detector_node
from .analysis.budget_monitor import budget_monitor_node
from .storage.db_save import db_save_node
from .output.summary_generator import summary_generator_node

logger = logging.getLogger(__name__)


# ============================================================================
# State 定義
# ============================================================================

class BookkeepingState(TypedDict, total=False):
    # 輸入
    user_id: int
    raw_text: str
    intent: str

    # Parser 輸出
    amount: float
    transaction_type: str
    description: str
    time_hint: Optional[str]
    merchant: Optional[str]
    parse_confidence: float
    parse_method: str

    # Classifier 輸出
    category_id: Optional[int]
    category_name: str

    # Anomaly 輸出
    is_anomaly: bool
    anomaly_reason: Optional[str]
    anomaly_severity: Optional[str]
    anomaly_suggestion: Optional[str]
    anomaly_stat_flag: Optional[str]
    anomaly_method: Optional[str]

    # Budget 輸出
    budget_warning: Optional[str]
    budget_level: Optional[str]
    budget_usage_pct: float
    budget_remaining: float
    budget_method: Optional[str]

    # DB 輸出
    transaction_id: Optional[str]
    db_success: bool

    # 最終輸出
    response_message: str
    error: Optional[str]


# ============================================================================
# 條件路由
# ============================================================================

def should_continue_after_parser(state: BookkeepingState) -> str:
    """Parser 後判斷：有錯誤就跳到 summary，否則繼續"""
    if state.get("error"):
        return "summary"
    return "classifier"


# ============================================================================
# 建立 Graph
# ============================================================================

def create_bookkeeping_graph():
    """
    建立記帳 LangGraph
    流程：parser → classifier → anomaly → budget → db_save → summary
    """
    workflow = StateGraph(BookkeepingState)

    # 加入所有 Node
    workflow.add_node("parser", transaction_parser_node)
    workflow.add_node("classifier", category_classifier_node)
    workflow.add_node("anomaly", anomaly_detector_node)
    workflow.add_node("budget", budget_monitor_node)
    workflow.add_node("db_save", db_save_node)
    workflow.add_node("summary", summary_generator_node)

    # 設定起點
    workflow.set_entry_point("parser")

    # 設定邊（流程）
    workflow.add_conditional_edges(
        "parser",
        should_continue_after_parser,
        {
            "classifier": "classifier",
            "summary": "summary",
        }
    )
    workflow.add_edge("classifier", "anomaly")
    workflow.add_edge("anomaly", "budget")
    workflow.add_edge("budget", "db_save")
    workflow.add_edge("db_save", "summary")
    workflow.add_edge("summary", END)

    # 編譯
    graph = workflow.compile()
    logger.info("✅ Bookkeeping LangGraph 編譯完成")

    return graph


# ============================================================================
# 執行入口
# ============================================================================

def run_bookkeeping(raw_text: str, user_id: int = 1) -> dict:
    """
    執行記帳流程
    輸入：用戶原始文字
    輸出：完整的 state（包含 response_message）
    """
    graph = create_bookkeeping_graph()

    initial_state = {
        "user_id": user_id,
        "raw_text": raw_text,
        "intent": "record",
    }

    result = graph.invoke(initial_state)
    return result