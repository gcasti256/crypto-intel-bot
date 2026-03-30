from __future__ import annotations

from typing import Any

import numpy as np

from crypto_intel.rag.embeddings import HashEmbedder


class VectorStore:
    def __init__(self, embedder: HashEmbedder | None = None) -> None:
        self.embedder = embedder or HashEmbedder()
        self._vectors: list[np.ndarray] = []
        self._documents: list[dict[str, Any]] = []

    def add(self, text: str, metadata: dict[str, Any] | None = None) -> None:
        vector = self.embedder.embed(text)
        self._vectors.append(vector)
        self._documents.append({"text": text, "metadata": metadata or {}})

    def add_batch(
        self, texts: list[str], metadatas: list[dict[str, Any]] | None = None
    ) -> None:
        metas = metadatas or [{} for _ in texts]
        for text, meta in zip(texts, metas):
            self.add(text, meta)

    def search(self, query: str, k: int = 5) -> list[dict[str, Any]]:
        if not self._vectors:
            return []

        query_vec = self.embedder.embed(query)
        matrix = np.array(self._vectors)

        similarities = matrix @ query_vec
        top_k = min(k, len(self._vectors))
        indices = np.argsort(similarities)[::-1][:top_k]

        results = []
        for idx in indices:
            score = float(similarities[idx])
            if score > 0:
                results.append({
                    "text": self._documents[idx]["text"],
                    "metadata": self._documents[idx]["metadata"],
                    "score": score,
                })
        return results

    def clear(self) -> None:
        self._vectors.clear()
        self._documents.clear()

    @property
    def size(self) -> int:
        return len(self._vectors)
