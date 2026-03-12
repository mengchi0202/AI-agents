from typing import Dict, Any

def taide_llm_runtime(prompt: str, max_tokens: int = 512) -> Dict[str, Any]:
    """
    Mock TAIDE runtime.
    後續你可以把這裡替換成真正的 TAIDE inference（本地/HTTP/Transformers）。
    """
    text = (
        "【TAIDE-MOCK 回覆】\n"
        "（以下為示意，代表模型已收到 prompt 並產生教學型回答）\n\n"
        f"{prompt.strip()[:1200]}"
    )
    return {
        "text": text,
        "model": "TAIDE-MOCK",
        "usage": {"max_tokens": max_tokens}
    }
