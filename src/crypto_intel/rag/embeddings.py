from __future__ import annotations

import hashlib
import math
import re

import numpy as np


class HashEmbedder:
    def __init__(self, dim: int = 256) -> None:
        self.dim = dim

    def _tokenize(self, text: str) -> list[str]:
        text = text.lower().strip()
        tokens = re.findall(r"\b\w+\b", text)
        return tokens

    def _hash_token(self, token: str) -> int:
        return int(hashlib.md5(token.encode()).hexdigest(), 16)

    def embed(self, text: str) -> np.ndarray:
        tokens = self._tokenize(text)
        if not tokens:
            return np.zeros(self.dim, dtype=np.float64)

        vector = np.zeros(self.dim, dtype=np.float64)
        token_counts: dict[str, int] = {}
        for t in tokens:
            token_counts[t] = token_counts.get(t, 0) + 1

        num_tokens = len(tokens)

        for token, count in token_counts.items():
            tf = count / num_tokens
            idf = math.log(1 + num_tokens / (1 + count))

            h = self._hash_token(token)
            idx = h % self.dim
            sign = 1.0 if (h // self.dim) % 2 == 0 else -1.0

            vector[idx] += sign * tf * idf

            idx2 = (h * 31) % self.dim
            vector[idx2] += sign * tf * idf * 0.5

        norm = np.linalg.norm(vector)
        if norm > 0:
            vector = vector / norm

        return vector

    def embed_batch(self, texts: list[str]) -> np.ndarray:
        return np.array([self.embed(text) for text in texts])
