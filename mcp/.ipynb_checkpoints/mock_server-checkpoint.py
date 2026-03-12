from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Any, Dict

from src.mcp.registry import register_tool, list_tools, call_tool

from src.mcp.tools.taide_llm_runtime import taide_llm_runtime
from src.mcp.tools.knowledge_kb_retrieve import knowledge_kb_retrieve
from src.mcp.tools.news_query import news_query

# ---- Register tools at import time ----
register_tool(
    name="taide_llm_runtime",
    description="TAIDE LLM 推論（mock）：輸入 prompt，輸出教學型文字回覆",
    input_schema={
        "type": "object",
        "properties": {
            "prompt": {"type": "string"},
            "max_tokens": {"type": "integer", "default": 512},
        },
        "required": ["prompt"],
    },
    output_schema={
        "type": "object",
        "properties": {
            "text": {"type": "string"},
            "model": {"type": "string"},
            "usage": {"type": "object"},
        },
    },
    handler=taide_llm_runtime,
)

register_tool(
    name="knowledge_kb_retrieve",
    description="金融內建 KB 檢索：輸入 query，回傳命中的 KB 條目",
    input_schema={
        "type": "object",
        "properties": {
            "query": {"type": "string"},
            "top_k": {"type": "integer", "default": 3},
        },
        "required": ["query"],
    },
    output_schema={
        "type": "object",
        "properties": {
            "hits": {"type": "array"},
            "query": {"type": "string"},
            "top_k": {"type": "integer"},
        },
    },
    handler=knowledge_kb_retrieve,
)

register_tool(
    name="news_query",
    description="新聞查詢（mock）：輸入 query，回傳台股/ETF 相關新聞列表",
    input_schema={
        "type": "object",
        "properties": {
            "query": {"type": "string"},
            "top_k": {"type": "integer", "default": 3},
            "market": {"type": "string", "default": "TW"},
            "focus": {"type": "string", "default": "ETF"},
        },
        "required": ["query"],
    },
    output_schema={
        "type": "object",
        "properties": {
            "articles": {"type": "array"},
            "query": {"type": "string"},
            "top_k": {"type": "integer"},
        },
    },
    handler=news_query,
)

# ---- FastAPI app ----
app = FastAPI(title="Mock MCP Server", version="0.1.0")

class ToolCallRequest(BaseModel):
    name: str
    arguments: Dict[str, Any] = {}

@app.get("/mcp/tools")
def mcp_list_tools():
    return list_tools()

@app.post("/mcp/tools/call")
def mcp_call_tool(req: ToolCallRequest):
    try:
        result = call_tool(req.name, req.arguments)
        return {"ok": True, "result": result}
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except TypeError as e:
        # wrong args / missing fields
        raise HTTPException(status_code=400, detail=f"Bad arguments: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
