#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
TAIDE Model Loader - FP32 版本
"""

import os
import torch
import logging
from transformers import AutoTokenizer, AutoModelForCausalLM

logger = logging.getLogger(__name__)


class TAIDEModel:
    """TAIDE 12B 模型 - FP32 精度（最穩定）"""
    
    def __init__(self, model_path: str = None):
        self.model_path = model_path or os.getenv("MODEL_PATH", "/var/lib/jenkins/taide-12b")
        self.tokenizer = None
        self.model = None
        self.is_loaded = False
    
    def load(self):
        """載入模型"""
        if self.is_loaded:
            logger.info("[TAIDE] 模型已載入")
            return
        
        try:
            logger.info("[TAIDE] 載入 Tokenizer...")
            self.tokenizer = AutoTokenizer.from_pretrained(
                self.model_path,
                trust_remote_code=True,
                token=os.getenv("HF_TOKEN")
            )
            
            # 修正 pad_token_id 問題
            if self.tokenizer.pad_token_id == 0:
                logger.warning("[TAIDE] ⚠️ pad_token_id=0 會導致問題，修正為 eos_token_id")
                self.tokenizer.pad_token_id = self.tokenizer.eos_token_id
                self.tokenizer.pad_token = self.tokenizer.eos_token
            
            logger.info(f"[TAIDE] pad_token_id: {self.tokenizer.pad_token_id}")
            logger.info(f"[TAIDE] eos_token_id: {self.tokenizer.eos_token_id}")
            
            # 載入模型 - 根據環境變數選擇精度
            logger.info("[TAIDE] 載入模型權重...")
            
            # 決定精度
            if os.getenv("USE_FP32", "true").lower() == "true":
                dtype = torch.float32
                logger.info("[TAIDE] 使用精度: FP32（最穩定，記憶體 ~50GB）")
            elif os.getenv("USE_BFLOAT16", "false").lower() == "true":
                dtype = torch.bfloat16
                logger.info("[TAIDE] 使用精度: BF16（平衡，記憶體 ~25GB）")
            else:
                dtype = torch.float16
                logger.info("[TAIDE] 使用精度: FP16（最快，但可能不穩定）")
            
            self.model = AutoModelForCausalLM.from_pretrained(
                self.model_path,
                trust_remote_code=True,
                token=os.getenv("HF_TOKEN"),
                device_map="auto",
                dtype=dtype,
            )
            
            self.is_loaded = True
            logger.info("[TAIDE] ✅ 模型載入成功")
            
            # 顯示記憶體使用
            if torch.cuda.is_available():
                allocated = torch.cuda.memory_allocated(0) / (1024**3)
                reserved = torch.cuda.memory_reserved(0) / (1024**3)
                total = torch.cuda.get_device_properties(0).total_memory / (1024**3)
                
                logger.info(f"[TAIDE] GPU 記憶體使用:")
                logger.info(f"  已分配: {allocated:.2f} GB")
                logger.info(f"  已保留: {reserved:.2f} GB")
                logger.info(f"  總容量: {total:.1f} GB")
                logger.info(f"  使用率: {(allocated/total)*100:.1f}%")
        
        except Exception as e:
            logger.error(f"[TAIDE] ❌ 模型載入失敗: {e}")
            import traceback
            traceback.print_exc()
            raise
    
    def generate(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_new_tokens: int = 256,
        top_p: float = 0.9,
        top_k: int = 50
    ) -> str:
        """生成回應"""
        if not self.is_loaded:
            logger.warning("[TAIDE] 模型未載入，自動載入中...")
            self.load()
        
        try:
            # Tokenize
            inputs = self.tokenizer(
                prompt,
                return_tensors="pt",
                padding=False,
            ).to(self.model.device)
            
            logger.debug(f"[TAIDE] Input tokens: {inputs.input_ids.shape[1]}")
            
            # 生成
            with torch.no_grad():
                outputs = self.model.generate(
                    inputs.input_ids,
                    max_new_tokens=max_new_tokens,
                    temperature=temperature,
                    top_p=top_p,
                    top_k=top_k,
                    do_sample=temperature > 0,
                    pad_token_id=self.tokenizer.pad_token_id,
                    eos_token_id=self.tokenizer.eos_token_id,
                )
            
            # 解碼（只取新生成的部分）
            generated_text = self.tokenizer.decode(
                outputs[0][inputs.input_ids.shape[1]:],
                skip_special_tokens=True
            )
            
            logger.debug(f"[TAIDE] Generated: {len(generated_text)} chars")
            
            return generated_text.strip()
        
        except Exception as e:
            logger.error(f"[TAIDE] 生成失敗: {e}")
            import traceback
            traceback.print_exc()
            raise
    
# ============================================================================
# 全域模型實例（單例模式）
# ============================================================================

_model_instance = None


def get_taide_model() -> TAIDEModel:
    """取得全域 TAIDE 模型實例"""
    global _model_instance
    
    if _model_instance is None:
        _model_instance = TAIDEModel()
    
    return _model_instance


# ============================================================================
# 測試
# ============================================================================

if __name__ == "__main__":
    import logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    print("=" * 80)
    print("TAIDE 模型測試（FP32）")
    print("=" * 80)
    
    model = get_taide_model()
    
    print("\n載入模型...")
    model.load()
    
    print("\n測試生成...")
    tests = [
        "你好",
        "請用一句話介紹台灣。",
        "台灣的首都是？",
    ]
    
    for i, prompt in enumerate(tests, 1):
        print(f"\n【測試 {i}】")
        print(f"提示: {prompt}")
        
        response = model.generate(prompt, temperature=0.7, max_new_tokens=100)
        
        print(f"回應: {response}")
        print("-" * 80)
    
    print("\n✅ 測試完成")
