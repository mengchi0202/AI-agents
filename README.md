AI-agents: Agentic 理財建議系統 🚀
基於 LangGraph 與 TAIDE 12B 的多代理人協作系統，為使用者提供客製化、具在地化溫度的投資理財建議。

🌟 核心特色
多代理人協作 (Multi-Agent Architecture)：利用 LangGraph 構建專家級節點（Goal Manager, Savings Advisor, Notifier），模擬人類理財顧問。

TAIDE 12B 整合：採用台灣在地化大語言模型 TAIDE，能精準理解並使用繁體中文金融術語，提供具台灣生活感的省錢建議。

RAG 知識增強：整合外部金融資訊與用戶歷史數據，有效抑制 LLM 的幻覺現象。

高效能數據持久化：

PostgreSQL: 存儲核心財務目標與交易一致性數據。

Redis: 實作 Checkpointer 機制，保存多輪對話狀態。

MongoDB: 存放非結構化 RAG 知識文件與詳細 Log。

🏗️ 系統架構圖
本專案採用非線性圖結構，確保每個 Agent 都能在正確的時機點介入處理。

程式碼片段
graph TD
    User((使用者)) --> Manager[Goal Manager Node]
    Manager --> Router{進度路由判斷}
    Router -- 進度落後/分析請求 --> Advisor[Savings Advisor Node]
    Router -- 資料同步 --> Notifier[Progress Notifier Node]
    Advisor -- AI 生成建議 --> Notifier
    Notifier --> User
    
    subgraph "數據層"
    Manager <--> PG[(PostgreSQL)]
    Advisor <--> TAIDE[[TAIDE 12B GPU]]
    Notifier <--> Redis[(Redis Cache)]
    end
🛠️ 技術棧 (Tech Stack)
Framework: LangGraph, LangChain

LLM: TAIDE 12B (Llama-based)

Language: Python 3.10+

Database: PostgreSQL, Redis, MongoDB

Infrastructure: Docker, AI-Stack (GPU Support)

📂 專案結構
Plaintext
.
├── src/
│   ├── agents/
│   │   └── goals/
│   │       ├── coordinator.py      # LangGraph 工作流定義 (中控)
│   │       ├── goal_manager.py     # 負責目標數據運算
│   │       ├── savings_advisor.py  # TAIDE 模型推理節點
│   │       └── progress_notifier.py # 最終結果彙整節點
│   ├── database/
│   │   └── crud.py                # 資料庫操作邏輯
│   └── state.py                    # 定義 TypedDict 狀態
├── tests/
│   └── test_goals.py               # 完整端到端測試腳本
└── .env                            # 環境變數設定
🚀 快速開始
1. 安裝依賴
Bash
pip install -r requirements.txt
2. 環境配置
建立 .env 檔案並填入資料庫連線資訊：

程式碼片段
DB_USER=your_user
DB_PASSWORD=your_password
DB_HOST=127.0.0.1
DB_NAME=your_db
3. 執行 Agent 測試
Bash
export PYTHONPATH=.
python3 tests/test_goals.py
📈 Demo 測試結果範例
當使用者設定了「日本京都旅遊」目標，系統會自動產出：

【日本京都旅遊 進度報告】
萬事起頭難，我們一起努力！💪
📊 目前達成率：10.0%
📉 剩餘缺口：$45,000

💡 理財教練小叮嚀：

減少外食頻率：京都美食多但餐廳貴，平時可多自煮或選擇平價店家。

善用交通卡：考慮購買京都市巴士一日券，並步行欣賞風景，省下計程車費。

