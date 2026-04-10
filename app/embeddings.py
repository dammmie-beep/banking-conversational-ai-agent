

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

    def search(self, query: str, top_k: int = 5, min_score: float = 0.28) -> List[str]:
        query_vec = self.model.encode(
            [query],
            convert_to_numpy=True,
            show_progress_bar=False
        ).astype(np.float32)
        faiss.normalize_L2(query_vec)
        scores, indices = self.index.search(query_vec, top_k)

        results = []
        for score, idx in zip(scores[0], indices[0]):
            log(f"[VectorStore] score={float(score):.4f} idx={idx}")
            if idx < len(self.texts) and float(score) >= min_score:
                results.append(self.texts[idx])

        return results


def chunk_text(text: str, chunk_size: int = 300, overlap: int = 50) -> List[str]:
    """
    Split text on blank-line paragraph boundaries so that product entries
    (description + features + benefits) stay together in one chunk.
    Falls back to word-count splitting only for very long paragraphs.
    """
    import re
    paras = [p.strip() for p in re.split(r'\n\s*\n', text) if p.strip()]

    chunks: List[str] = []
    buffer: List[str] = []
    buffer_words = 0

    for para in paras:
        para_words = len(para.split())
        # If adding this paragraph would exceed the chunk size, flush buffer first
        if buffer_words + para_words > chunk_size and buffer:
            chunks.append("\n\n".join(buffer))
            # Keep last paragraph as overlap context
            if overlap > 0:
                buffer = [buffer[-1]]
                buffer_words = len(buffer[0].split())
            else:
                buffer = []
                buffer_words = 0
        buffer.append(para)
        buffer_words += para_words

    if buffer:
        chunks.append("\n\n".join(buffer))

    return chunks