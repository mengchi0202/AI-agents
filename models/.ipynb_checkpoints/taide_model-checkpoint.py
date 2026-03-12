#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
TAIDE Model Loader - Llama3 格式修正版
"""

import os
import torch
import logging
from typing import Optional
from transformers import (
    AutoTokenizer,
    AutoModelForCausalLM,
)

logger = logging.getLogger(__name__)


class TAIDEModel:
    """TAIDE 12B 模型 - Llama3 格式"""
    
    def __init__(
        self,
        model_name: str = None,
        model_path: str = None,
        load_in_4bit: bool = False,
        device: str = "auto"
    ):
        self.model_path = model_path or os.getenv("MODEL_PATH", "/var/lib/jenkins/taide-12b")
        self.load_in_4bit = load_in_4bit
        self.device = device
        
        self.tokenizer = None
        self.model = None
        self.is_loaded = False
        
        logger.info(f"[TAIDE] 模型路徑: {self.model_path}")
    
    def load(self):
        """載入模型"""
        if self.is_loaded:
            return
        
        try:
            logger.info("[TAIDE] 載入 Tokenizer...")
            self.tokenizer = AutoTokenizer.from_pretrained(
                self.model_path,
                trust_remote_code=True,
                token=os.getenv("HF_TOKEN")
            )
            
            # 設定 pad token
            if self.tokenizer.pad_token is None:
                self.tokenizer.pad_token = self.tokenizer.eos_token
            
            logger.info("[TAIDE] 載入模型...")
            self.model = AutoModelForCausalLM.from_pretrained(
                self.model_path,
                trust_remote_code=True,
                token=os.getenv("HF_TOKEN"),
                device_map=self.device,
                dtype=torch.float16,
            )
            
            self.is_loaded = True
            logger.info("[TAIDE] ✅ 模型載入成功")
            
            if torch.cuda.is_available():
                allocated = torch.cuda.memory_allocated(0) / (1024**3)
                total = torch.cuda.get_device_properties(0).total_memory / (1024**3)
                logger.info(f"[TAIDE] GPU: {allocated:.2f} GB / {total:.1f} GB")
            
        except Exception as e:
            logger.error(f"[TAIDE] 載入失敗: {e}")
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
            self.load()
        
        try:
            # Llama3 格式的 prompt（TAIDE 是基於 Llama3）
            formatted_prompt = f"""<|begin_of_text|><|start_header_id|>user<|end_header_id|>

{prompt}<|eot_id|><|start_header_id|>assistant<|end_header_id|>

"""
            
            logger.debug(f"[TAIDE] Prompt:\n{formatted_prompt}")
            
            # Tokenize
            inputs = self.tokenizer(
                formatted_prompt,
                return_tensors="pt",
                add_special_tokens=False  # 我們已經手動加了
            ).to(self.model.device)
            
            logger.debug(f"[TAIDE] Input tokens: {inputs['input_ids'].shape[1]}")
            
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
            
            # 只解碼新生成的部分
            input_length = inputs.input_ids.shape[1]
            generated_ids = outputs[0][input_length:]
            
            generated_text = self.tokenizer.decode(
                generated_ids,
                skip_special_tokens=True
            )
            
            logger.debug(f"[TAIDE] Generated: {generated_text[:100]}...")
            
            return generated_text.strip()
        
        except Exception as e:
            logger.error(f"[TAIDE] 生成失敗: {e}")
            raise
    
    def unload(self):
        """卸載模型"""
        if self.model:
            del self.model
        if self.tokenizer:
            del self.tokenizer
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        self.is_loaded = False


_model_instance = None

def get_taide_model() -> TAIDEModel:
    global _model_instance
    if _model_instance is None:
        _model_instance = TAIDEModel()
    return _model_instance
