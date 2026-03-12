"""
Bookkeeping API 路由
"""
from typing import Optional
from fastapi import APIRouter
from pydantic import BaseModel

from ...agents.bookkeeping import BookkeepingCoordinator
from ...agents.base import Task

router = APIRouter()


class RecordRequest(BaseModel):
    """記帳請求"""
    text: str
    user_id: str = "default"


class RecordResponse(BaseModel):
    """記帳回應"""
    success: bool
    message: str
    data: Optional[dict] = None


@router.post("/record", response_model=RecordResponse)
async def record_transaction(request: RecordRequest):
    """記錄交易"""
    coordinator = BookkeepingCoordinator()
    
    task = Task.create(
        input_data={
            "intent": "record",
            "text": request.text,
            "user_id": request.user_id,
        }
    )
    
    result = await coordinator.execute(task)
    
    if result.error:
        return RecordResponse(
            success=False,
            message=result.error,
        )
    
    return RecordResponse(
        success=True,
        message="記帳成功",
        data=result.result,
    )


@router.get("/summary")
async def get_summary(user_id: str = "default", period: str = "today"):
    """取得消費摘要"""
    coordinator = BookkeepingCoordinator()
    
    task = Task.create(
        input_data={
            "intent": "query",
            "query_type": "summary",
            "user_id": user_id,
            "period": period,
        }
    )
    
    result = await coordinator.execute(task)
    
    return {
        "success": not result.error,
        "data": result.result,
    }
