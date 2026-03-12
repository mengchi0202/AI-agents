"""
Transaction Parser Agent
交易解析 Agent - 將自然語言轉為結構化交易資料
"""
import json
import re
from datetime import datetime, timedelta
from typing import Any, Dict, Optional
from dataclasses import dataclass, asdict

from ...base import BaseAgent, AgentCard, Task, Artifact
from ....models import get_taide_model


# ============================================================================
# 資料結構
# ============================================================================

@dataclass
class ParsedTransaction:
    """解析後的交易"""
    amount: float
    transaction_type: str  # expense / income
    description: str
    time_hint: Optional[str] = None
    merchant: Optional[str] = None
    category: Optional[str] = None
    confidence: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


# ============================================================================
# 常數
# ============================================================================

# 金額提取 patterns
AMOUNT_PATTERNS = [
    r'(\d+(?:,\d{3})*(?:\.\d+)?)\s*(?:元|塊|$)',
    r'(?:NT\$?|＄)\s*(\d+(?:,\d{3})*(?:\.\d+)?)',
    r'(?:花了|付了|買了|繳了|吃了|用了|刷了|喝了)\s*(\d+(?:,\d{3})*(?:\.\d+)?)',
    r'共\s*(\d+(?:,\d{3})*(?:\.\d+)?)',
]

# 收入關鍵字
INCOME_KEYWORDS = [
    "薪水", "薪資", "工資", "入帳", "收入", "獎金", "紅包",
    "退款", "回饋", "利息", "股利", "分紅", "稿費", "接案",
    "兼職", "打工", "報酬", "進帳", "領到", "拿到", "拿到", 
    "家教", "投資收益", "賣出", "出售", "賣掉", "賣了",
]

# 時間關鍵字
TIME_KEYWORDS = {
    "今天": 0, "今日": 0, "剛剛": 0, "剛才": 0,
    "昨天": -1, "昨日": -1,
    "前天": -2, "大前天": -3,
}

# LLM Prompt
PARSE_PROMPT = """你是一個記帳助手，專門解析用戶的記帳輸入。

請解析以下記帳內容，提取交易資訊。

用戶輸入：{user_input}

請以 JSON 格式回答，包含以下欄位：
- amount: 金額（純數字）
- transaction_type: "expense" 或 "income"
- description: 簡短描述（2-10字）
- time_hint: 時間提示（如「今天」「午餐」，若無則 null）
- merchant: 商家名稱（若無則 null）

只回覆 JSON，不要其他文字。"""


# ============================================================================
# Transaction Parser Agent
# ============================================================================

class TransactionParserAgent(BaseAgent):
    """
    交易解析 Agent
    將自然語言記帳輸入解析為結構化交易資料。
    規則優先，複雜情況在調用 LLM。
    """
    
    def __init__(self):
        super().__init__()
        self._model = None
    
    @property
    def agent_card(self) -> AgentCard:
        return AgentCard(
            name="transaction_parser",
            description="解析自然語言記帳輸入，提取交易資訊",
            capabilities=["parse_transaction", "extract_amount", "detect_merchant"],
            version="1.0.0",
        )
    
    async def process(self, task: Task) -> Artifact:
        """處理解析任務"""
        text = task.input.get("text", "")
        
        if not text:
            return Artifact(
                type="error",
                data={"message": "輸入文字為空"},
            )
        
        # 先嘗試規則解析
        result = self._rule_based_parse(text)
        
        if result and result.confidence >= 0.8:
            return Artifact(
                type="parsed_transaction",
                data=result.to_dict(),
                metadata={"method": "rule_based"},
            )
        
        # 規則解析信心度不夠，使用 LLM
        llm_result = await self._llm_parse(text)
        
        # 如果 LLM 也失敗，返回規則結果
        if llm_result.get("amount", 0) == 0 and result:
            return Artifact(
                type="parsed_transaction",
                data=result.to_dict(),
                metadata={"method": "rule_based_fallback"},
            )
        
        return Artifact(
            type="parsed_transaction",
            data=llm_result,
            metadata={"method": "llm"},
        )
    

    # 規則解析
    def _rule_based_parse(self, text: str) -> Optional[ParsedTransaction]:
  
        # 提取金額
        amount = self._extract_amount(text)
        if amount is None:
            return None
        
        # 判斷收支類型
        transaction_type = self._detect_transaction_type(text)
        
        # 提取時間
        time_hint = self._extract_time_hint(text)
        
        # 提取商家
        merchant = self._extract_merchant(text)
        
        # 生成描述
        description = self._generate_description(text, amount, merchant)
        
        # 計算信心度
        confidence = 0.7
        if merchant:
            confidence += 0.1
        if time_hint:
            confidence += 0.1
        
        return ParsedTransaction(
            amount=amount,
            transaction_type=transaction_type,
            description=description,
            time_hint=time_hint,
            merchant=merchant,
            confidence=min(confidence, 1.0),
        )
    
    def _extract_amount(self, text: str) -> Optional[float]:
        """提取金額"""
        for pattern in AMOUNT_PATTERNS:
            match = re.search(pattern, text)
            if match:
                amount_str = match.group(1).replace(",", "")
                try:
                    return float(amount_str)
                except ValueError:
                    continue
        
        # 簡單數字匹配
        match = re.search(r'(\d+(?:\.\d+)?)', text)
        if match:
            try:
                return float(match.group(1))
            except ValueError:
                pass
        
        return None
    
    def _detect_transaction_type(self, text: str) -> str:
        """判斷收支類型"""
        for keyword in INCOME_KEYWORDS:
            if keyword in text:
                return "income"
        return "expense"
    
    def _extract_time_hint(self, text: str) -> Optional[str]:
        """提取時間提示"""
        for keyword in TIME_KEYWORDS.keys():
            if keyword in text:
                return keyword
        
        # 餐點時間
        meals = ["早餐", "午餐", "晚餐", "宵夜", "下午茶", "早午餐","點心"]
        for meal in meals:
            if meal in text:
                return meal
        
        return None
    
    def _extract_merchant(self, text: str) -> Optional[str]:
        """提取商家名稱"""
        # 常見商家
        merchants = [
            "麥當勞", "肯德基", "星巴克", "全家", "7-11", "統一超商",
            "全聯", "家樂福", "好市多", "IKEA", "鼎泰豐", "王品",
            "摩斯漢堡", "漢堡王", "必勝客", "達美樂", "路易莎",
            "cama", "85度C", "50嵐", "清心", "迷客夏", "可不可",
            "Uber", "Uber Eats", "Foodpanda", "台灣大哥大", 
            "遠傳電信", "中華電信", "台灣之星", "LINE Pay", "街口支付", "Apple Store",
            "Google Play", "蝦皮", "露天拍賣", "Yahoo奇摩拍賣", "PChome"
            ,"momo","博客來","誠品書店","金石堂","燦坤","光南","大潤發","愛買","家樂福"
            
        ]
        
        for merchant in merchants:
            if merchant.lower() in text.lower():
                return merchant
        
        # 嘗試「在 XXX」格式
        match = re.search(r'在\s*([^\s,，。]+?)\s*(?:吃|買|花|消費)', text)
        if match:
            return match.group(1)
        
        return None
    
    def _generate_description(self, text: str, amount: float, merchant: Optional[str]) -> str:
        """生成描述"""
        # 移除金額
        desc = re.sub(r'\d+(?:,\d{3})*(?:\.\d+)?\s*(?:元|塊)?', '', text)
        # 移除常見詞
        desc = re.sub(r'(花了|付了|買了|繳了|喝了|今天|昨天|剛剛|在)', '', desc)
        desc = desc.strip()
        
        if not desc and merchant:
            return merchant
        
        return desc[:20] if desc else "消費"
    
    # ========================================================================
    # LLM 解析
    # ========================================================================
    
    async def _llm_parse(self, text: str) -> Dict[str, Any]:
        """使用 LLM 解析"""
        try:
            if self._model is None:
                self._model = get_taide_model()
                self._model.load()
            
            prompt = PARSE_PROMPT.format(user_input=text)
            response = self._model.generate(prompt, temperature=0.1, max_new_tokens=256)
            
            # 解析 JSON
            return self._parse_json_response(response, text)
            
        except Exception as e:
            # LLM 失敗，返回基本結果
            return {
                "amount": 0,
                "transaction_type": "expense",
                "description": text[:20],
                "time_hint": None,
                "merchant": None,
                "error": str(e),
            }
    
    def _parse_json_response(self, response: str, original_text: str) -> Dict[str, Any]:
        """解析 LLM 的 JSON 回應"""
        try:
            # 清理 markdown 格式
            cleaned = response.strip()
            if cleaned.startswith("```"):
                cleaned = cleaned.split("```")[1]
                if cleaned.startswith("json"):
                    cleaned = cleaned[4:]
            cleaned = cleaned.strip()
            
            result = json.loads(cleaned)
            
            # 確保必要欄位存在
            return {
                "amount": float(result.get("amount", 0)),
                "transaction_type": result.get("transaction_type", "expense"),
                "description": result.get("description", original_text[:20]),
                "time_hint": result.get("time_hint"),
                "merchant": result.get("merchant"),
                "confidence": 0.85,
            }
            
        except (json.JSONDecodeError, ValueError):
            return {
                "amount": 0,
                "transaction_type": "expense",
                "description": original_text[:20],
                "time_hint": None,
                "merchant": None,
                "parse_error": True,
            }