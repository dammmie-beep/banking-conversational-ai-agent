

# # app/embeddings.py
# import faiss
# import numpy as np
# from typing import List
# from sentence_transformers import SentenceTransformer
# from config import Config


# def log(msg: str):
#     import sys
#     try:
#         sys.__stdout__.write(msg + "\n")
#         sys.__stdout__.flush()
#     except OSError:
#         with open("agent.log", "a") as f:
#             f.write(msg + "\n")


# class VectorStore:
#     def __init__(self, texts: List[str]):
#         log("[VectorStore] Loading embedding model...")
#         self.model = SentenceTransformer(Config.EMBEDDING_MODEL)
#         self.texts = texts
#         self.index = self._build_index(texts)
#         log(f"[VectorStore] Indexed {len(texts)} chunks.")

#     def _build_index(self, texts: List[str]):
#         embeddings = self.model.encode(
#             texts,
#             convert_to_numpy=True,
#             show_progress_bar=False    # ← disable progress bar to avoid stdout issues
#         )
#         embeddings = embeddings.astype(np.float32)
#         faiss.normalize_L2(embeddings)
#         dim = embeddings.shape[1]
#         index = faiss.IndexFlatIP(dim)
#         index.add(embeddings)
#         return index

#     def search(self, query: str, top_k: int = 3) -> List[str]:
#         query_vec = self.model.encode(
#             [query],
#             convert_to_numpy=True,
#             show_progress_bar=False    # ← disable here too
#         ).astype(np.float32)
#         faiss.normalize_L2(query_vec)
#         scores, indices = self.index.search(query_vec, top_k)
#         return [self.texts[i] for i in indices[0] if i < len(self.texts)]


# def chunk_text(text: str, chunk_size: int = 300, overlap: int = 50) -> List[str]:
#     words = text.split()
#     chunks = []
#     for i in range(0, len(words), chunk_size - overlap):
#         chunk = " ".join(words[i:i + chunk_size])
#         if chunk:
#             chunks.append(chunk)
#     return chunks

# app/embeddings.py
import os
import faiss
import numpy as np
from typing import List

# Silence all transformer output before importing
os.environ["TOKENIZERS_PARALLELISM"] = "false"
os.environ["TRANSFORMERS_VERBOSITY"] = "error"

from sentence_transformers import SentenceTransformer
from config import Config


def log(msg: str):
    import sys
    try:
        sys.__stdout__.write(msg + "\n")
        sys.__stdout__.flush()
    except OSError:
        with open("agent.log", "a") as f:
            f.write(msg + "\n")


class VectorStore:
    def __init__(self, texts: List[str]):
        log("[VectorStore] Loading embedding model...")

        # Suppress all logging from sentence_transformers
        import logging
        logging.getLogger("sentence_transformers").setLevel(logging.ERROR)
        logging.getLogger("transformers").setLevel(logging.ERROR)

        self.model = SentenceTransformer(
            Config.EMBEDDING_MODEL,
            device="cpu"
        )
        self.texts = texts
        self.index = self._build_index(texts)
        log(f"[VectorStore] Indexed {len(texts)} chunks.")

    def _build_index(self, texts: List[str]):
        embeddings = self.model.encode(
            texts,
            convert_to_numpy=True,
            show_progress_bar=False,
            batch_size=32
        )
        embeddings = embeddings.astype(np.float32)
        faiss.normalize_L2(embeddings)
        dim = embeddings.shape[1]
        index = faiss.IndexFlatIP(dim)
        index.add(embeddings)
        return index

    def search(self, query: str, top_k: int = 3) -> List[str]:
        query_vec = self.model.encode(
            [query],
            convert_to_numpy=True,
            show_progress_bar=False
        ).astype(np.float32)
        faiss.normalize_L2(query_vec)
        scores, indices = self.index.search(query_vec, top_k)
        return [self.texts[i] for i in indices[0] if i < len(self.texts)]


def chunk_text(text: str, chunk_size: int = 300, overlap: int = 50) -> List[str]:
    words = text.split()
    chunks = []
    for i in range(0, len(words), chunk_size - overlap):
        chunk = " ".join(words[i:i + chunk_size])
        if chunk:
            chunks.append(chunk)
    return chunks