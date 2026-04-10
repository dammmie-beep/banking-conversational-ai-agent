# config.py
import os

class Config:
    # Paths
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    MODEL_PATH = os.path.join(BASE_DIR, "models", "qwen2.5-3b-instruct-q4_k_m.gguf")
    # EXCEL_PATH = os.path.join(BASE_DIR, "data", "Globus_AI_Engr_Interview_Data.xlsx")
    DB_PATH = os.path.join(BASE_DIR, "data", "banking.db")
    PRODUCTS_PATH = os.path.join(BASE_DIR, "data", "Product_Information.txt")

    # LLM settings
    N_CTX = 2048           # Context window (reduced — 10-turn window never needs 4096)
    N_THREADS = 4          # CPU threads (match nproc)
    MAX_TOKENS = 150       # Max response tokens (trimmed — 200 rarely needed)
    TEMPERATURE = 0.3      # Lower = faster, more deterministic
    N_BATCH = 512          # Prompt eval batch size (was 64 — bigger = faster prefill)

    # Embedding model (downloaded once, cached offline)
    # EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
    EMBEDDING_MODEL = "./models/minilm" 

    # Sliding window
    WINDOW_SIZE = 10       # Number of turn-pairs to retain