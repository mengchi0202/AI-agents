import json
import re
from typing import Any, Dict


def extract_json_object(text: str) -> Dict[str, Any]:
    """
    從模型輸出中抓出第一個 JSON object。
    若整段就是 JSON，直接 parse。
    否則用 regex 抓 {...}。
    """
    text = (text or "").strip()
    if not text:
        raise ValueError("empty_response")

    # 先直接 parse
    try:
        return json.loads(text)
    except Exception:
        pass

    # 再抓第一個 JSON object
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        raise ValueError("no_json_object_found")

    return json.loads(match.group(0))