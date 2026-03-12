from __future__ import annotations

# -----------------------------
# News trigger keywords
# 只有明確要求新聞/近期消息時才應該開 news
# -----------------------------
NEWS_TRIGGER_KEYWORDS = [
    "新聞",
    "最新消息",
    "近期消息",
    "最近新聞",
    "近期新聞",
    "新聞摘要",
    "有沒有新聞",
    "相關新聞",
    "最近怎麼了",
    "發生什麼事",
    "最近發生什麼",
    "最新發展",
    "最新動態",
    "新聞怎麼看",
    "最近有什麼消息",
    "近期有什麼消息",
]

# -----------------------------
# Question patterns
# 用來判斷 question_type
# -----------------------------
QUESTION_PATTERNS = {
    "definition": [
        "是什麼",
        "什麼是",
        "意思是什麼",
        "代表什麼",
        "定義",
    ],
    "comparison": [
        "差在哪",
        "差別",
        "有什麼不同",
        "哪個比較好",
        "比較",
    ],
    "risk": [
        "風險",
        "缺點",
        "壞處",
        "有問題嗎",
        "危險嗎",
    ],
    "timing": [
        "現在適合",
        "適合進場嗎",
        "現在可以買嗎",
        "現在能買嗎",
        "現在好嗎",
    ],
    "reasoning": [
        "為什麼",
        "原因",
        "怎麼會",
        "怎麼了",
        "影響",
        "會不會",
        "前景",
        "看法",
    ],
    "news_query": [
        "新聞",
        "最新消息",
        "近期消息",
        "最近新聞",
        "最近怎麼了",
        "發生什麼事",
    ],
    "recommendation": [
        "推薦",
        "適合買什麼",
        "新手適合",
        "怎麼選",
        "哪個好",
    ],
}

# -----------------------------
# 台灣金融常見概念詞
# category -> terms
# -----------------------------
FINANCE_TERMS_BY_CATEGORY = {
    "basic_investing": [
        "投資",
        "資產配置",
        "分散風險",
        "長期投資",
        "定期定額",
        "單筆投資",
        "複利",
        "報酬率",
        "風險報酬比",
        "波動",
        "停損",
        "停利",
        "本金",
        "現金流",
        "被動收入",
    ],
    "stocks": [
        "股票",
        "個股",
        "台股",
        "美股",
        "科技股",
        "電子股",
        "金融股",
        "傳產股",
        "概念股",
        "成長股",
        "價值股",
        "權值股",
        "中小型股",
        "防禦型股票",
        "景氣循環股",
    ],
    "etf": [
        "ETF",
        "台股ETF",
        "美股ETF",
        "高股息ETF",
        "市值型ETF",
        "債券ETF",
        "槓桿ETF",
        "反向ETF",
        "主動式ETF",
        "被動式ETF",
        "ETF配息",
        "ETF淨值",
        "ETF折溢價",
        "ETF費用率",
        "ETF追蹤誤差",
    ],
    "taiwan_etf": [
        "0050",
        "0056",
        "006208",
        "00692",
        "00878",
        "00919",
        "00929",
        "00940",
        "00713",
        "00679B",
        "00687B",
        "國泰永續高股息",
        "元大台灣50",
        "元大高股息",
        "富邦台50",
    ],
    "bonds": [
        "債券",
        "公債",
        "公司債",
        "投資等級債",
        "非投資等級債",
        "高收益債",
        "債券ETF",
        "殖利率",
        "到期殖利率",
        "票面利率",
        "存續期間",
        "違約風險",
        "利率風險",
    ],
    "macro": [
        "通膨",
        "CPI",
        "PPI",
        "升息",
        "降息",
        "利率",
        "實質利率",
        "聯準會",
        "Fed",
        "央行",
        "貨幣政策",
        "景氣循環",
        "衰退",
        "經濟成長",
        "GDP",
        "失業率",
        "美元指數",
        "匯率",
        "台幣",
        "美債",
    ],
    "fundamentals": [
        "財報",
        "營收",
        "毛利率",
        "營業利益率",
        "淨利率",
        "EPS",
        "本益比",
        "PER",
        "股價淨值比",
        "PBR",
        "ROE",
        "ROA",
        "自由現金流",
        "現金股利",
        "股利",
        "配息",
        "配股",
        "除息",
        "填息",
        "庫藏股",
    ],
    "technical": [
        "技術分析",
        "均線",
        "月線",
        "季線",
        "年線",
        "KD",
        "MACD",
        "RSI",
        "支撐",
        "壓力",
        "突破",
        "跌破",
        "成交量",
        "爆量",
        "量縮",
        "多頭",
        "空頭",
    ],
    "market_events": [
        "股災",
        "崩盤",
        "修正",
        "反彈",
        "牛市",
        "熊市",
        "回檔",
        "財報季",
        "除權息",
        "法說會",
        "營收公布",
        "財測",
        "地緣政治",
        "戰爭風險",
        "黑天鵝",
    ],
    "sectors": [
        "半導體",
        "AI",
        "伺服器",
        "晶圓代工",
        "封測",
        "IC設計",
        "記憶體",
        "面板",
        "航運",
        "鋼鐵",
        "金融",
        "能源",
        "生技",
        "電動車",
        "綠能",
    ],
    "famous_companies": [
        "台積電",
        "聯發科",
        "鴻海",
        "廣達",
        "緯創",
        "英業達",
        "華碩",
        "技嘉",
        "日月光",
        "中信金",
        "國泰金",
        "富邦金",
        "兆豐金",
        "台達電",
        "聯電",
        "NVIDIA",
        "Apple",
        "Microsoft",
        "Tesla",
        "AMD",
    ],
}

# -----------------------------
# Synonyms / aliases
# 用來把不同問法統一成標準概念
# -----------------------------
TERM_ALIASES = {
    "etf": "ETF",
    "Etf": "ETF",
    "fed": "聯準會",
    "聯準會升息": "升息",
    "聯準會降息": "降息",
    "高股息": "高股息ETF",
    "台灣50": "0050",
    "元大台灣50": "0050",
    "元大高股息": "0056",
    "國泰永續高股息": "00878",
    "市值型": "市值型ETF",
    "債券etf": "債券ETF",
    "殖利率高": "殖利率",
    "配股配息": "股利",
    "美國升息": "升息",
    "美國降息": "降息",
    "大盤": "台股",
    "加權指數": "台股",
    "那指": "NASDAQ",
    "費半": "半導體",
}

# -----------------------------
# 常見台灣金融問題（可用來做 heuristic / few-shot tag）
# -----------------------------
COMMON_TW_FINANCE_QUESTIONS = [
    "ETF是什麼",
    "0050是什麼",
    "0056是什麼",
    "00878是什麼",
    "00919是什麼",
    "高股息ETF適合長期投資嗎",
    "0050跟0056差在哪",
    "市值型ETF和高股息ETF差在哪",
    "債券ETF為什麼會跌",
    "殖利率越高越好嗎",
    "配息高代表比較好嗎",
    "升息對股市有什麼影響",
    "降息對債券有什麼影響",
    "通膨對投資有什麼影響",
    "本益比是什麼",
    "ROE是什麼",
    "EPS是什麼",
    "什麼是資產配置",
    "新手適合買什麼ETF",
    "定期定額適合0050嗎",
    "現在適合買台股嗎",
    "科技股前景好嗎",
    "台積電現在還能買嗎",
    "金融股適合存股嗎",
    "高股息ETF有什麼風險",
    "今天股市怎麼了",
    "最近台股發生什麼事",
    "最近AI概念股怎麼了",
    "最近有沒有台積電的新聞",
]

# -----------------------------
# 扁平化後的 keyword set
# 方便快速 matching
# -----------------------------
ALL_FINANCE_TERMS = sorted({
    term
    for terms in FINANCE_TERMS_BY_CATEGORY.values()
    for term in terms
})


def normalize_term(term: str) -> str:
    if not term:
        return term
    t = term.strip()
    return TERM_ALIASES.get(t, TERM_ALIASES.get(t.lower(), t))


def detect_news_trigger(text: str) -> bool:
    text = (text or "").strip()
    return any(k in text for k in NEWS_TRIGGER_KEYWORDS)


def extract_lexicon_concepts(text: str, max_terms: int = 5) -> list[str]:
    """
    用簡單字串比對做 fallback 概念抽取。
    後續 understanding.py 可直接用這個。
    """
    text = (text or "").strip()
    found: list[str] = []
    seen = set()

    for term in ALL_FINANCE_TERMS:
        if term and term in text:
            norm = normalize_term(term)
            if norm not in seen:
                seen.add(norm)
                found.append(norm)
                if len(found) >= max_terms:
                    return found

    for alias, canonical in TERM_ALIASES.items():
        if alias and alias in text:
            norm = normalize_term(canonical)
            if norm not in seen:
                seen.add(norm)
                found.append(norm)
                if len(found) >= max_terms:
                    return found

    return found


def detect_question_type(text: str) -> str:
    text = (text or "").strip()

    for qtype, patterns in QUESTION_PATTERNS.items():
        if any(p in text for p in patterns):
            return qtype

    return "general"