"""Embedding backends. The hashing backend is deterministic and does not download weights."""

import hashlib
from typing import Protocol

import numpy as np

from app.core.text import tokens
from app.inference.gate import GATE


class Embedder(Protocol):
    dim: int
    name: str

    def embed(self, texts: list[str], *, is_query: bool = False) -> np.ndarray:
        ...


class HashingEmbedder:
    name = "hash"
    dim = 256

    def embed(self, texts: list[str], *, is_query: bool = False) -> np.ndarray:
        rows = np.zeros((len(texts), self.dim), dtype="float32")
        for index, text in enumerate(texts):
            for token in tokens(text):
                digest = hashlib.sha256(token.encode("utf-8")).digest()
                bucket = int.from_bytes(digest[:4], "little") % self.dim
                sign = 1.0 if digest[4] % 2 == 0 else -1.0
                rows[index, bucket] += sign
        norms = np.linalg.norm(rows, axis=1, keepdims=True)
        norms[norms == 0] = 1.0
        return rows / norms


class E5Embedder:
    """CPU multilingual embedder. Imported lazily so tests do not require torch."""

    name = "e5"

    def __init__(self, model_name: str):
        from sentence_transformers import SentenceTransformer

        self.model_name = model_name
        self.model = SentenceTransformer(model_name, device="cpu")
        self.dim = int(self.model.get_sentence_embedding_dimension())

    def embed(self, texts: list[str], *, is_query: bool = False) -> np.ndarray:
        GATE.acquire("embeddings")
        try:
            prefix = "query: " if is_query else "passage: "
            prepared = [prefix + text for text in texts]
            vectors = self.model.encode(prepared, normalize_embeddings=True, show_progress_bar=False)
            return np.asarray(vectors, dtype="float32")
        finally:
            GATE.release("embeddings")


def build_embedder(backend: str, model_name: str) -> Embedder:
    if backend == "hash":
        return HashingEmbedder()
    if backend == "e5":
        return E5Embedder(model_name)
    raise ValueError(f"Unknown embedding backend: {backend}")
