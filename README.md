
# 🚀 多代理人個人化理財管理系統

本平台是一個整合多個 AI Agents 的個人化財務管理系統，結合**記帳、預算控管、短期儲蓄規劃與投資建議**。特別針對學生族群設計，旨在降低理財門檻、提升財務自律，並透過台灣在地化大模型 **TAIDE** 確保理財建議符合台灣金融環境與文化語境。

## 📌 專案核心動機

1. **解決學生痛點**：針對資金有限、缺乏投資知識、消費自制力不足及財務規劃能力缺失等問題。
2. **標準化協作 (A2A & MCP)**：引入 A2A 與 MCP 協議，解決 LLM 上下文標準化缺失及異質代理人間的通訊障礙。
3. **數位主權與在地化**：使用 **TAIDE** 模型，精準理解台灣特有金融術語（如：台股 ETF、高股息標的）。

---

## 🏗️ 系統架構 

本系統採用 **LangGraph** 框架實現多代理人協作，將複雜的財務處理拆解為專責節點：

### 1. 記帳領域 

負責日常收支的結構化處理。

* **Bookkeeping Coordinator**: 主協調器，負責意圖分派。
* **Transaction Parser**: 將自然語言轉為結構化 JSON（如：「今天吃麥噹噹 150」）。
* **Anomaly Detector**: 偵測異常消費（例如：超過歷史平均 2 個標準差）。
* **Budget Monitor**: 監控預算進度（50%/75%/90%/100% 分級警告）。

### 2. 目標領域 

協助建立與追蹤儲蓄目標。

* **Goal Manager**: 計算達成率、資金缺口及理想進度（expected_rate）。
* **Savings Advisor**: 向使用者生成具體開源節流建議。
* **Progress Notifier**: 主動提醒使用者目前儲蓄進度，將數據轉化為溫暖、具台灣語感的鼓勵訊息。

### 3. 金額知識領域 

基於 **RAG ** 的諮詢專家。

* **Knowledge Retriever**: 從 PostgreSQL + pgvector 檢索台股與 ETF 知識。
* **News Adapter**: 透過 A2A 協議橋接新聞子圖，獲取即時市場動態。
  
### 4. 投資建議領域 
---

### 核心技術
| 技術 | 用途 | 說明 |
|------|------|------|
| **TAIDE-LX-7B** | LLM | 繁體中文語言模型，用於所有語意理解任務 |
| **LangGraph** | Agent 框架 | 將 Agent 設計為 Node，透過 State 流轉資料 |
| **A2A Protocol** | Agent 間通訊 | 跨 Domain Agent 協作（如記帳→目標追蹤） |
| **MCP** | 工具協議 | Agent 呼叫外部工具（DB 查詢、寫入等） |
| **FastAPI** | 後端 | API 服務 |
| **PostgreSQL** | 主資料庫 | 使用者、交易、預算、目標 |
| **MongoDB** | 彈性儲存 | 對話狀態、日誌、事件、新聞 |
| **Redis** | 快取 | Session、預算快取、限流 |

### 設計原則
- 所有 Node 皆使用 **TAIDE LLM** 進行語意理解，不使用 rule-based
- 各 Node 透過 **BookkeepingState** 共享狀態流轉
- 跨 Domain 通訊採用 **A2A Protocol**，各 Domain 獨立開發
- DB 尚未連上的 Node 使用 **Mock 數據**，之後替換

## 💾 資料庫架構
### PostgreSQL（結構化數據）

儲存核心業務資料，使用純 SQL + psycopg2 操作。

| 資料表 | 用途 |
|--------|------|
| users | 使用者資料（LINE ID、姓名、生日、性別） |
| categories | 消費分類（17 個預設分類含子分類） |
| transactions | 交易記錄（收入/支出） |
| budgets | 預算管理 |
| financial_goals | 財務目標追蹤 |

### MongoDB（彈性數據）

| Collection | 用途 |
|------------|------|
| conversation_states | Agent 對話狀態 |
| llm_logs | LLM 解析日誌 |
| events | 事件總線（Agent 間通訊記錄） |
| financial_news | 財經新聞 |
| user_behaviors | 使用者行為記錄 |

### Redis（快取與即時數據）

| 功能 | Key 格式 | 過期時間 |
|------|----------|----------|
| 使用者 Session | `session:{user_id}` | 30 分鐘 |
| 預算快取 | `budget:{user_id}` | 1 小時 |
| 分類快取 | `categories:all` | 24 小時 |
| 當日消費總額 | `daily_total:{user_id}:{date}` | 2 小時 |

* **基礎設施**: 雲端 AI-Stack (GPU 資源部署)

---

## 📊 預期成果

1. **驗證 A2A/MCP 範式**：建立一套可供台灣在地 AI 應用參考的開發模式。
2. **在地化知識庫**：建構結構化的台股、ETF 投資百科。
3. **行為改善**：預期提升使用者 40% 以上的記帳持續率與預算達成度。

---

### 💡 專案亮點筆記 (For Interviewer/Recruiter)

* **技術深度**：使用了最新的 MCP 協議解決 Tool 使用的標準化問題，並透過 LangGraph 的 `Conditional Edges` 實現複雜的路由判斷。
* **在地化優勢**：不同於一般 GPT 應用，本專案深度整合 TAIDE，解決台灣特有金融場景（如：0050, 00878 等 ETF）的理解痛點。
* **數據科學應用**：在異常偵測節點中結合了統計學規則（平均值 ± 標準差）與 LLM 語意判斷。
