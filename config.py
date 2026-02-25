# config.py
import os

class Config:
    # Paths
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    MODEL_PATH = os.path.join(BASE_DIR, "models", "smollm2-1.7b-instruct-q4_k_m.gguf")
    # EXCEL_PATH = os.path.join(BASE_DIR, "data", "Globus_AI_Engr_Interview_Data.xlsx")
    DB_PATH = os.path.join(BASE_DIR, "data", "banking.db")
    PRODUCTS_PATH = os.path.join(BASE_DIR, "data", "product_Information.txt")

    # LLM settings
    N_CTX = 4096           # Context window
    N_THREADS = 4          # CPU threads
    MAX_TOKENS = 512       # Max response tokens
    TEMPERATURE = 0.2    # Low
    N_BATCH = 64 

    # Embedding model (downloaded once, cached offline)
    # EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
    EMBEDDING_MODEL = "./models/minilm" 

    # Sliding window
    WINDOW_SIZE = 10       # Number of turn-pairs to retain