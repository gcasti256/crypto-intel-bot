from __future__ import annotations

import numpy as np

from crypto_intel.rag.embeddings import HashEmbedder
from crypto_intel.rag.retriever import Retriever
from crypto_intel.rag.store import VectorStore


class TestHashEmbedder:
    def test_embed_produces_correct_dim(self):
        embedder = HashEmbedder(dim=256)
        vec = embedder.embed("hello world")
        assert vec.shape == (256,)

    def test_embed_is_normalized(self):
        embedder = HashEmbedder()
        vec = embedder.embed("bitcoin price analysis")
        norm = np.linalg.norm(vec)
        assert abs(norm - 1.0) < 1e-6

    def test_embed_empty_string(self):
        embedder = HashEmbedder()
        vec = embedder.embed("")
        assert np.all(vec == 0)

    def test_embed_deterministic(self):
        embedder = HashEmbedder()
        v1 = embedder.embed("test sentence")
        v2 = embedder.embed("test sentence")
        np.testing.assert_array_equal(v1, v2)

    def test_embed_batch(self):
        embedder = HashEmbedder()
        texts = ["hello", "world", "test"]
        batch = embedder.embed_batch(texts)
        assert batch.shape == (3, 256)

    def test_similar_texts_closer(self):
        embedder = HashEmbedder()
        v1 = embedder.embed("bitcoin price surges to new high")
        v2 = embedder.embed("bitcoin price reaches record level")
        v3 = embedder.embed("the weather forecast for tomorrow")

        sim_12 = np.dot(v1, v2)
        sim_13 = np.dot(v1, v3)
        assert sim_12 > sim_13


class TestVectorStore:
    def test_add_and_search(self):
        store = VectorStore()
        store.add("Bitcoin hits new high", {"source": "news"})
        store.add("Ethereum upgrade complete", {"source": "news"})
        store.add("Python programming tutorial", {"source": "blog"})

        results = store.search("Bitcoin price", k=2)
        assert len(results) <= 2
        assert results[0]["text"] == "Bitcoin hits new high"

    def test_empty_store_search(self):
        store = VectorStore()
        results = store.search("anything")
        assert results == []

    def test_store_size(self):
        store = VectorStore()
        assert store.size == 0
        store.add("doc1")
        store.add("doc2")
        assert store.size == 2

    def test_clear(self):
        store = VectorStore()
        store.add("doc1")
        store.add("doc2")
        store.clear()
        assert store.size == 0

    def test_add_batch(self):
        store = VectorStore()
        store.add_batch(
            ["doc1", "doc2", "doc3"],
            [{"id": 1}, {"id": 2}, {"id": 3}],
        )
        assert store.size == 3


class TestRetriever:
    def test_retrieve(self, sample_articles):
        retriever = Retriever()
        retriever.add_articles(sample_articles)
        results = retriever.retrieve("bitcoin price", k=3)
        assert len(results) <= 3
        assert isinstance(results[0], str)

    def test_retrieve_with_metadata(self, sample_articles):
        retriever = Retriever()
        retriever.add_articles(sample_articles)
        results = retriever.retrieve_with_metadata("ethereum etf", k=2)
        assert len(results) <= 2
        if results:
            assert "metadata" in results[0]

    def test_empty_retriever(self):
        retriever = Retriever()
        results = retriever.retrieve("anything")
        assert results == []

    def test_clear_retriever(self, sample_articles):
        retriever = Retriever()
        retriever.add_articles(sample_articles)
        assert retriever.store.size > 0
        retriever.clear()
        assert retriever.store.size == 0
