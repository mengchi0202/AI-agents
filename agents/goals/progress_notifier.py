def progress_notifier_node(state: dict):
    if state.get("error"):
        return {"response_message": f"❌ 錯誤：{state.get('error')}"}

    # --- Step 1: 數據準備 ---
    metrics = state.get("metrics", {})
    goal_name = state.get("goal_name", "目標")
    completion_rate = metrics.get('completion_rate', 0)
    gap_amount = int(metrics.get('gap', 0))
    # 這裡就是你問的：從筆記本的 advice_options 這一頁把建議拿出來
    advice_list = state.get("advice_options", [])
    is_lagging = state.get("is_lagging", False)

    # --- Step 2: 根據達成率給予稱讚 (對應你的任務指令 1) ---
    if completion_rate >= 100:
        praise = "恭喜達成！你太強了！🏆"
    elif completion_rate >= 75:
        praise = "給自己個掌聲，終點就在眼前了！🌟"
    elif completion_rate >= 50:
        praise = "一半了！這進度讚啦，穩紮穩打！👍"
    elif completion_rate >= 25:
        praise = "不錯喔，已經跨出關鍵的一大步了！🔥"
    else:
        praise = "萬事起頭難，我們一起努力！💪"

    # --- Step 3: 組裝最終訊息 (對應你的任務指令 2, 3, 4) ---
    # 基礎進度報告
    header = f"【{goal_name} 進度報告】\n{praise}\n"
    stats = f"📊 目前達成率：{completion_rate}%\n📉 剩餘缺口：${gap_amount:,}\n"
    
    # 處理 AI 建議 (如果是落後，就把 advisor 產生的那段溫暖文字接上)
    if is_lagging and advice_list:
        # advice_list[0] 裡面就是 TAIDE 產生的「飲料、便當」建議
        ai_content = f"\n💡 理財教練小叮嚀：\n{advice_list[0]}"
    else:
        ai_content = "\n目前進度非常標準，請繼續保持目前的存錢節奏喔！✨"

    final_response = header + stats + ai_content

    # --- Step 4: 最終回傳 ---
    # 這樣 response_message 就會包含所有資訊了！
    return {"response_message": final_response}