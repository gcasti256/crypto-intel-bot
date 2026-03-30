from __future__ import annotations

from typing import Any

from crypto_intel.rag.store import VectorStore


class Retriever:
    def __init__(self, store: VectorStore | None = None) -> None:
        self.store = store or VectorStore()

    def add_articles(self, articles: list[dict[str, Any]]) -> None:
        for article in articles:
            text = f"{article.get('title', '')}. {article.get('summary', '')}"
            self.store.add(text, metadata=article)

    def retrieve(self, query: str, k: int = 5) -> list[str]:
        results = self.store.search(query, k=k)
        return [r["text"] for r in results]

    def retrieve_with_metadata(
        self, query: str, k: int = 5
    ) -> list[dict[str, Any]]:
        return self.store.search(query, k=k)

    def clear(self) -> None:
        self.store.clear()
