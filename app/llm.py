# app/llm.py
import sys
from llama_cpp import Llama
from typing import Dict, List, Optional
from config import Config


def log(msg: str):
    try:
        sys.__stdout__.write(msg + "\n")
        sys.__stdout__.flush()
    except OSError:
        with open("agent.log", "a") as f:
            f.write(msg + "\n")


class LLMWrapper:
    def __init__(self):
        log("[LLM] Loading ...")
        self.llm = Llama(
            model_path=Config.MODEL_PATH,
            n_ctx=Config.N_CTX,
            n_threads=Config.N_THREADS,
            n_gpu_layers=0,
            n_batch=Config.N_BATCH,
            chat_format="chatml",
            verbose=False,
            use_mmap=True,
            use_mlock=False,
        )
        log("[LLM] Loaded successfully.")

    def chat(
        self,
        messages: List[Dict],
        system_prompt: str,
        max_tokens: Optional[int] = None,
    ) -> str:
        """
        Build a ChatML-formatted chat completion.
        Uses create_chat_completion so llama.cpp applies the correct
        <|im_start|>/<|im_end|> tokens for SmolLM2-Instruct.
        """
        recent_messages = messages[-10:]
        chat_messages = [{"role": "system", "content": system_prompt.strip()}]
        chat_messages.extend(recent_messages)

        log(f"[LLM] Sending {len(chat_messages)} messages ({max_tokens or Config.MAX_TOKENS} max tokens)...")

        response = self.llm.create_chat_completion(
            messages=chat_messages,
            max_tokens=max_tokens if max_tokens is not None else Config.MAX_TOKENS,
            temperature=Config.TEMPERATURE,
        )

        result = response["choices"][0]["message"]["content"].strip()
        log(f"[LLM] Response: {result[:120]}")
        return result


# Singleton
llm_wrapper = LLMWrapper()
