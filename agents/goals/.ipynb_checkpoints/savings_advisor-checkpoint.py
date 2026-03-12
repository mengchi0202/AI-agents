from transformers import AutoModelForCausalLM, AutoTokenizer
import torch

# 1. 載入模型 (這會用到 AI-Stack 的 GPU)
model_path = "./taide-12b"
tokenizer = AutoTokenizer.from_pretrained(model_path)
model = AutoModelForCausalLM.from_pretrained(
    model_path, 
    torch_dtype=torch.bfloat16, 
    device_map="auto"
)
def savings_advisor_node(state: dict):
    metrics = state.get("metrics", {})
    daily = int(metrics.get("daily_needed", 0))
    goal_name = state.get("goal_name")
    current_response = state.get("response_message", "")

    # 1. 製作指令 (Prompt) - 加入 TAIDE 特有的對話格式（如果有的話）
    prompt = f"你是一個專業的理財教練。使用者目前的目標是「{goal_name}」，" \
             f"接下來每天需要多存 {daily} 元才能達成目標。" \
             f"請提供兩個具體且生活化的省錢建議，語氣要親切且鼓勵使用者。直接輸出建議內容即可。"

    # 2. 讓 TAIDE 開始思考
    inputs = tokenizer(prompt, return_tensors="pt").to("cuda")
    
    # 設定 generate 參數，避免太囉唆或斷掉
    outputs = model.generate(
        **inputs, 
        max_new_tokens=200,
        do_sample=True,
        temperature=0.7,
        top_p=0.9,
        repetition_penalty=1.2
    )
    
    # 3. 關鍵修正：只解碼「AI 生成」的部分，去掉 Prompt
    # inputs.input_ids.shape[1] 是 Prompt 的長度
    gen_text = tokenizer.decode(outputs[0][inputs.input_ids.shape[1]:], skip_special_tokens=True).strip()

    # 4. 組合最終訊息
    # 把原本的數據報告，加上 AI 溫馨的建議
    final_message = f"{current_response}\n\n💡 AI 教練的建議：\n{gen_text}"
    
    return {
        "advice_options": [gen_text],
        "response_message": final_message  # 覆蓋原本的訊息，加入 AI 內容
    }
