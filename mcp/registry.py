from typing import Any, Callable, Dict

# Tool handler type
ToolFn = Callable[..., Dict[str, Any]]

TOOL_REGISTRY: Dict[str, Dict[str, Any]] = {}

def register_tool(
    name: str,
    description: str,
    input_schema: Dict[str, Any],
    output_schema: Dict[str, Any],
    handler: ToolFn,
) -> None:
    TOOL_REGISTRY[name] = {
        "name": name,
        "description": description,
        "input_schema": input_schema,
        "output_schema": output_schema,
        "handler": handler,
    }

def list_tools() -> Dict[str, Any]:
    return {
        "tools": [
            {
                "name": t["name"],
                "description": t["description"],
                "input_schema": t["input_schema"],
                "output_schema": t["output_schema"],
            }
            for t in TOOL_REGISTRY.values()
        ]
    }

def call_tool(name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
    if name not in TOOL_REGISTRY:
        raise KeyError(f"Tool not found: {name}")
    handler: ToolFn = TOOL_REGISTRY[name]["handler"]
    return handler(**(arguments or {}))
