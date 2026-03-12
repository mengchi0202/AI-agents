"""
Bookkeeping Coordinator Agent
記帳領域協調器
Bookkeeping Coordinator Agent（舊版 - 已被 graph.py 取代）

   此檔案為早期 class-based 設計，
   現在的記帳流程改用 LangGraph 實作：
   - src/agents/bookkeeping/graph.py（LangGraph 版本）
   
   保留此檔案作為設計 記錄原始的 A2A AgentCard 定義。
"""
from typing import Any, Dict, Optional
from ..base import BaseAgent, AgentCard, Task, Artifact, TaskStatus


class BookkeepingCoordinator(BaseAgent):
    """記帳領域協調器"""
    
    @property
    def agent_card(self) -> AgentCard:
        return AgentCard(
            name="bookkeeping_coordinator",
            description="記帳領域協調器，處理所有記帳相關請求",
            capabilities=[
                "record_transaction",
                "query_transactions",
                "analyze_spending",
                "categorize_expense",
            ],
            dependencies=[
                "transaction_parser",
                "category_classifier",
                "anomaly_detector",
                "summary_generator",
            ],
        )
    
    async def process(self, task: Task) -> Artifact:
        """處理記帳任務"""
        intent = task.input.get("intent", "record")
        
        if intent == "record":
            return await self._handle_record(task)
        elif intent == "query":
            return await self._handle_query(task)
        elif intent == "analyze":
            return await self._handle_analyze(task)
        else:
            return Artifact(
                type="error",
                data={"message": f"Unknown intent: {intent}"},
            )
    
    async def _handle_record(self, task: Task) -> Artifact:
        """處理記帳請求"""
        text = task.input.get("text", "")
        
        # TODO: 呼叫 Transaction Parser Agent
        # TODO: 呼叫 Category Classifier Agent
        # TODO: 儲存到資料庫
        
        return Artifact(
            type="transaction_recorded",
            data={
                "message": f"已記錄: {text}",
                "parsed": {
                    "amount": 0,
                    "category": "pending",
                    "description": text,
                },
            },
        )
    
    async def _handle_query(self, task: Task) -> Artifact:
        """處理查詢請求"""
        query_type = task.input.get("query_type", "summary")
        
        # TODO: 呼叫 Summary Generator Agent
        
        return Artifact(
            type="query_result",
            data={
                "query_type": query_type,
                "result": "查詢功能開發中",
            },
        )
    
    async def _handle_analyze(self, task: Task) -> Artifact:
        """處理分析請求"""
        # TODO: 呼叫 Spending Pattern Analyzer Agent
        
        return Artifact(
            type="analysis_result",
            data={
                "analysis": "分析功能開發中",
            },
        )