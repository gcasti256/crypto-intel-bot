from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest

from crypto_intel.agents.market_data_agent import market_data_agent, set_client
from crypto_intel.agents.report_agent import report_agent, set_llm_provider
from crypto_intel.agents.sentiment_agent import (
    compute_keyword_sentiment,
    configure,
    sentiment_agent,
)
from crypto_intel.agents.state import AnalysisState
from crypto_intel.agents.technical_agent import technical_agent


def _make_state(**overrides: Any) -> AnalysisState:
    base: AnalysisState = {
        "token": "btc",
        "token_id": "",
        "price_data": {},
        "price_history": [],
        "technical_indicators": {},
        "news_articles": [],
        "sentiment_score": 0.0,
        "relevant_context": [],
        "analysis_summary": "",
        "risk_level": "medium",
        "confidence": 0.5,
    }
    base.update(overrides)  # type: ignore[typeddict-item]
    return base


class TestMarketDataAgent:
    @pytest.mark.asyncio
    async def test_fetches_data(self, sample_price_data, sample_price_history):
        mock_client = MagicMock()
        mock_client.resolve_token.return_value = "bitcoin"
        mock_client.get_price = AsyncMock(return_value=sample_price_data)
        mock_client.get_market_chart = AsyncMock(return_value=sample_price_history)
        set_client(mock_client)

        state = _make_state(token="btc")
        result = await market_data_agent(state)

        assert result["token_id"] == "bitcoin"
        assert result["price_data"]["price"] == 65432.10
        assert len(result["price_history"]) == 336

    @pytest.mark.asyncio
    async def test_searches_unknown_token(self, sample_price_data, sample_price_history):
        mock_client = MagicMock()
        mock_client.resolve_token.return_value = "unknown"
        mock_client.search_token = AsyncMock(return_value="some-coin")
        mock_client.get_price = AsyncMock(return_value=sample_price_data)
        mock_client.get_market_chart = AsyncMock(return_value=sample_price_history)
        set_client(mock_client)

        state = _make_state(token="unknown")
        result = await market_data_agent(state)

        assert result["token_id"] == "some-coin"


class TestTechnicalAgent:
    @pytest.mark.asyncio
    async def test_computes_indicators(self, sample_price_history):
        state = _make_state(price_history=sample_price_history)
        result = await technical_agent(state)

        indicators = result["technical_indicators"]
        assert "rsi" in indicators
        assert "macd_line" in indicators
        assert "signal" in indicators
        assert indicators["signal"] in ("bullish", "bearish", "neutral")

    @pytest.mark.asyncio
    async def test_handles_short_history(self):
        short_history = [{"timestamp": i, "price": 100 + i} for i in range(10)]
        state = _make_state(price_history=short_history)
        result = await technical_agent(state)

        indicators = result["technical_indicators"]
        assert indicators["rsi"] == 50.0
        assert indicators["signal"] == "neutral"


class TestSentimentAgent:
    def test_keyword_sentiment_positive(self, sample_articles):
        btc_articles = [a for a in sample_articles if "Bitcoin" in a["title"]]
        score = compute_keyword_sentiment(btc_articles)
        assert score > 0

    def test_keyword_sentiment_negative(self):
        articles = [
            {"title": "Market Crash Warning", "summary": "Bearish crash dump plunge fear"},
        ]
        score = compute_keyword_sentiment(articles)
        assert score < 0

    def test_keyword_sentiment_empty(self):
        score = compute_keyword_sentiment([])
        assert score == 0.0

    @pytest.mark.asyncio
    async def test_sentiment_agent_with_articles(self, sample_articles):
        from crypto_intel.data.news import NewsFetcher
        from crypto_intel.rag.retriever import Retriever

        mock_fetcher = MagicMock(spec=NewsFetcher)
        mock_fetcher.fetch_all = AsyncMock(return_value=sample_articles)
        configure(news_fetcher=mock_fetcher, retriever=Retriever())

        state = _make_state(token="btc", news_articles=sample_articles)
        result = await sentiment_agent(state)

        assert "sentiment_score" in result
        assert -1.0 <= result["sentiment_score"] <= 1.0
        assert len(result.get("relevant_context", [])) >= 0


class TestReportAgent:
    @pytest.mark.asyncio
    async def test_generates_report(self, sample_price_data):
        set_llm_provider(None)

        state = _make_state(
            token="btc",
            price_data=sample_price_data,
            technical_indicators={
                "rsi": 55.0,
                "signal": "bullish",
                "macd_histogram": [0.5],
                "sma_50": [64000.0],
                "bb_upper": [67000.0],
                "bb_lower": [63000.0],
                "current_price": 65432.10,
            },
            sentiment_score=0.3,
        )
        result = await report_agent(state)

        assert result["risk_level"] in ("low", "medium", "high")
        assert 0.0 <= result["confidence"] <= 1.0
        assert len(result["analysis_summary"]) > 0
        assert "BTC" in result["analysis_summary"]

    @pytest.mark.asyncio
    async def test_risk_levels(self):
        set_llm_provider(None)

        bearish_state = _make_state(
            token="btc",
            price_data={"price": 60000, "change_24h": -5},
            technical_indicators={"rsi": 85, "signal": "bearish"},
            sentiment_score=-0.5,
        )
        result = await report_agent(bearish_state)
        assert result["risk_level"] == "high"


class TestFullPipeline:
    @pytest.mark.asyncio
    async def test_end_to_end(self, sample_price_data, sample_price_history, sample_articles):
        mock_client = MagicMock()
        mock_client.resolve_token.return_value = "bitcoin"
        mock_client.get_price = AsyncMock(return_value=sample_price_data)
        mock_client.get_market_chart = AsyncMock(return_value=sample_price_history)
        set_client(mock_client)

        mock_fetcher = MagicMock()
        mock_fetcher.fetch_all = AsyncMock(return_value=sample_articles)
        configure(news_fetcher=mock_fetcher)
        set_llm_provider(None)

        from crypto_intel.agents.orchestrator import run_analysis

        result = await run_analysis("btc")

        assert result["token_id"] == "bitcoin"
        assert result["price_data"]["price"] == 65432.10
        assert result["risk_level"] in ("low", "medium", "high")
        assert len(result["analysis_summary"]) > 0
        assert result["technical_indicators"]["signal"] in (
            "bullish",
            "bearish",
            "neutral",
        )
