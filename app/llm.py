# # # # # app/llm.py
# # # # from llama_cpp import Llama
# # # # from config import Config

# # # # class LLMWrapper:
# # # #     def __init__(self):
# # # #         print("[LLM] Loading model... this may take 30–60 seconds.")
# # # #         self.llm = Llama(
# # # #             model_path=Config.MODEL_PATH,
# # # #             n_ctx=Config.N_CTX,
# # # #             n_threads=Config.N_THREADS,
# # # #             n_gpu_layers=0,     # CPU only
# # # #             verbose=False
# # # #         )
# # # #         print("[LLM] Model loaded.")

# # # #     def chat(self, messages: list[dict], system_prompt: str) -> str:
# # # #         """
# # # #         Format messages into a prompt string compatible with Phi-3 chat template.
# # # #         Phi-3 uses: <|system|>...<|end|><|user|>...<|end|><|assistant|>
# # # #         """
# # # #         prompt = f"<|system|>\n{system_prompt}<|end|>\n"
# # # #         for msg in messages:
# # # #             if msg["role"] == "user":
# # # #                 prompt += f"<|user|>\n{msg['content']}<|end|>\n"
# # # #             elif msg["role"] == "assistant":
# # # #                 prompt += f"<|assistant|>\n{msg['content']}<|end|>\n"
# # # #         prompt += "<|assistant|>\n"

# # # #         response = self.llm(
# # # #             prompt,
# # # #             max_tokens=Config.MAX_TOKENS,
# # # #             temperature=Config.TEMPERATURE,
# # # #             stop=["<|end|>", "<|user|>"]
# # # #         )
# # # #         return response["choices"][0]["text"].strip()


# # # # # Singleton
# # # # llm_wrapper = LLMWrapper()

# # # # app/llm.py
# # # from llama_cpp import Llama
# # # from typing import List, Dict  # ← add this import
# # # from config import Config

# # # class LLMWrapper:
# # #     def __init__(self):
# # #         print("[LLM] Loading model... this may take 30–60 seconds.")
# # #         self.llm = Llama(
# # #             model_path=Config.MODEL_PATH,
# # #             n_ctx=Config.N_CTX,
# # #             n_threads=Config.N_THREADS,
# # #             n_gpu_layers=0,
# # #             verbose=False
# # #         )
# # #         print("[LLM] Model loaded.")

# # #     def chat(self, messages: List[Dict], system_prompt: str) -> str:  # ← List[Dict] not list[dict]
# # #         prompt = f"<|system|>\n{system_prompt}<|end|>\n"
# # #         for msg in messages:
# # #             if msg["role"] == "user":
# # #                 prompt += f"<|user|>\n{msg['content']}<|end|>\n"
# # #             elif msg["role"] == "assistant":
# # #                 prompt += f"<|assistant|>\n{msg['content']}<|end|>\n"
# # #         prompt += "<|assistant|>\n"

# # #         response = self.llm(
# # #             prompt,
# # #             max_tokens=Config.MAX_TOKENS,
# # #             temperature=Config.TEMPERATURE,
# # #             stop=["<|end|>", "<|user|>"]
# # #         )
# # #         return response["choices"][0]["text"].strip()


# # # # Singleton
# # # llm_wrapper = LLMWrapper()

# # # app/llm.py
# # import os
# # import sys
# # from llama_cpp import Llama
# # from typing import List, Dict
# # from config import Config


# # class LLMWrapper:
# #     def __init__(self):
# #         print("[LLM] Loading model... this may take 30-60 seconds.", flush=True)
        
# #         # Fix for Windows console handle issue
# #         # Redirect C-level stdout/stderr during model load
# #         devnull = open(os.devnull, 'w')
# #         old_stdout = sys.stdout
# #         old_stderr = sys.stderr

# #         try:
# #             sys.stdout = devnull
# #             sys.stderr = devnull

# #             self.llm = Llama(
# #                 model_path=Config.MODEL_PATH,
# #                 n_ctx=Config.N_CTX,
# #                 n_threads=Config.N_THREADS,
# #                 n_gpu_layers=0,
# #                 verbose=False,
# #                 logits_all=False,
# #             )
# #         finally:
# #             # Always restore stdout/stderr even if loading fails
# #             sys.stdout = old_stdout
# #             sys.stderr = old_stderr
# #             devnull.close()

# #         print("[LLM] Model loaded successfully.", flush=True)

# #     def chat(self, messages: List[Dict], system_prompt: str) -> str:
# #         prompt = f"<|system|>\n{system_prompt}<|end|>\n"
# #         for msg in messages:
# #             if msg["role"] == "user":
# #                 prompt += f"<|user|>\n{msg['content']}<|end|>\n"
# #             elif msg["role"] == "assistant":
# #                 prompt += f"<|assistant|>\n{msg['content']}<|end|>\n"
# #         prompt += "<|assistant|>\n"

# #         response = self.llm(
# #             prompt,
# #             max_tokens=Config.MAX_TOKENS,
# #             temperature=Config.TEMPERATURE,
# #             stop=["<|end|>", "<|user|>"]
# #         )
# #         return response["choices"][0]["text"].strip()


# # # Singleton
# # llm_wrapper = LLMWrapper()

# # app/llm.py
# import os
# import sys
# import ctypes
# from llama_cpp import Llama
# from typing import List, Dict
# from config import Config


# class LLMWrapper:
#     def __init__(self):
#         # Write directly to original stdout before any redirection
#         sys.__stdout__.write("[LLM] Loading model... this may take 30-60 seconds.\n")
#         sys.__stdout__.flush()

#         self.llm = Llama(
#             model_path=Config.MODEL_PATH,
#             n_ctx=Config.N_CTX,
#             n_threads=Config.N_THREADS,
#             n_gpu_layers=0,
#             verbose=False,
#             logits_all=False,
#         )

#         sys.__stdout__.write("[LLM] Model loaded successfully.\n")
#         sys.__stdout__.flush()

#     def chat(self, messages: List[Dict], system_prompt: str) -> str:
#         prompt = f"<|system|>\n{system_prompt}<|end|>\n"
#         for msg in messages:
#             if msg["role"] == "user":
#                 prompt += f"<|user|>\n{msg['content']}<|end|>\n"
#             elif msg["role"] == "assistant":
#                 prompt += f"<|assistant|>\n{msg['content']}<|end|>\n"
#         prompt += "<|assistant|>\n"

#         response = self.llm(
#             prompt,
#             max_tokens=Config.MAX_TOKENS,
#             temperature=Config.TEMPERATURE,
#             stop=["<|end|>", "<|user|>"]
#         )
#         return response["choices"][0]["text"].strip()


# # Singleton
# # llm_wrapper = LLMWrapper()

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
        prompt = f"<|system|>\n{system_prompt}</s>\n"

        recent_messages = messages[-4:]
        for msg in recent_messages:
            if msg["role"] == "user":
                prompt += f"<|user|>\n{msg['content']}</s>\n"
            elif msg["role"] == "assistant":
                prompt += f"<|assistant|>\n{msg['content']}</s>\n"
        prompt += "<|assistant|>\n"

        log(f"[LLM] Sending prompt ({len(prompt.split())} words)...")

        response = self.llm(
            prompt,
            max_tokens=Config.MAX_TOKENS,
            temperature=Config.TEMPERATURE,
            stop=["</s>", "<|user|>", "<|system|>"],
            echo=False,
        )

        result = response["choices"][0]["text"].strip()
        log(f"[LLM] Response received: {result[:100]}")
        return result


# Singleton
llm_wrapper = LLMWrapper()