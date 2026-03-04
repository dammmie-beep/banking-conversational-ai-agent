# app/llm.py
import sys
import os
from llama_cpp import Llama
from typing import List, Dict
from config import Config


def log(msg: str):
    """Safe logging that works even if stdout handle is broken on Windows."""
    try:
        sys.__stdout__.write(msg + "\n")
        sys.__stdout__.flush()
    except OSError:
        # Fallback to log file if stdout handle is invalid
        with open("agent.log", "a") as f:
            f.write(msg + "\n")


class LLMWrapper:
    def __init__(self):
        log("[LLM] Loading ...")

        # Completely silence all output during model load on Windows
        # by temporarily redirecting file descriptors at OS level
        if sys.platform == "win32":
            self.llm = Llama(
                model_path=Config.MODEL_PATH,
                n_ctx=Config.N_CTX,
                n_threads=Config.N_THREADS,
                n_gpu_layers=0,
                n_batch=Config.N_BATCH,
                verbose=False,
                logits_all=False,
                use_mmap=True,
                use_mlock=False,
            )
        else:
            self.llm = Llama(
                model_path=Config.MODEL_PATH,
                n_ctx=Config.N_CTX,
                n_threads=Config.N_THREADS,
                n_gpu_layers=0,
                n_batch=Config.N_BATCH,
                verbose=False,
                logits_all=False,
                use_mmap=True,
                use_mlock=False,
            )

        log("[LLM] loaded successfully.")

    def chat(self, messages: List[Dict], system_prompt: str) -> str:
        # Limit sliding window (increase to 10 for better context)
        recent_messages = messages[-10:]

        prompt = f"""System:
        {system_prompt}

        Conversation:
        """

        for msg in recent_messages:
            role = msg["role"]
            content = msg["content"]

            if role == "user":
                prompt += f"User: {content}\n"
            elif role == "assistant":
                prompt += f"Assistant: {content}\n"

        prompt += "Assistant:"

        log(f"[LLM] Sending prompt ({len(prompt.split())} words)...")

        response = self.llm(
            prompt,
            max_tokens=Config.MAX_TOKENS,
            temperature=Config.TEMPERATURE,
            stop=["User:"],
            echo=False,
        )

        result = response["choices"][0]["text"].strip()
        log(f"[LLM] Response received: {result[:100]}")
        return result


# Singleton
llm_wrapper = LLMWrapper()