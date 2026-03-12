#!/usr/bin/env python3
from typing import TypedDict, Optional

class BookkeepingState(TypedDict, total=False):
    user_id: int
    raw_text: str
    intent: str
    amount: float
    transaction_type: str
    description: str
    time_hint: Optional[str]
    merchant: Optional[str]
    transaction_date: str
    parse_confidence: float
    parse_method: str
    category_id: Optional[int]
    category_name: str
    is_anomaly: bool
    anomaly_reason: Optional[str]
    anomaly_severity: Optional[str]
    anomaly_suggestion: Optional[str]
    anomaly_stat_flag: Optional[str]
    anomaly_method: Optional[str]
    budget_warning: Optional[str]
    budget_level: Optional[str]
    budget_usage_pct: float
    budget_remaining: float
    budget_method: Optional[str]
    transaction_id: Optional[str]
    db_success: bool
    response_message: str
    error: Optional[str]
