from __future__ import annotations

import datetime
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest


@pytest.fixture
def sample_price_data() -> dict[str, Any]:
    return {
        "price": 65432.10,
        "market_cap": 1_280_000_000_000,
        "volume_24h": 28_500_000_000,
        "change_24h": 2.35,
    }


@pytest.fixture
def sample_price_history() -> list[dict[str, float]]:
    import math

    base = 65000.0
    return [
        {"timestamp": 1700000000 + i * 3600, "price": base + 500 * math.sin(i / 10)}
        for i in range(336)  # 14 days of hourly data
    ]


@pytest.fixture
def sample_prices() -> list[float]:
    import math

    base = 65000.0
    return [base + 500 * math.sin(i / 10) for i in range(100)]


@pytest.fixture
def sample_articles() -> list[dict[str, Any]]:
    return [
        {
            "title": "Bitcoin Surges Past $65K as Institutional Adoption Grows",
            "summary": "Major institutions continue to accumulate Bitcoin, driving bullish momentum.",
            "link": "https://example.com/1",
            "published": datetime.datetime.now() - datetime.timedelta(hours=2),
            "source": "https://coindesk.com/rss",
        },
        {
            "title": "Ethereum ETF Approval Sparks Rally in Crypto Markets",
            "summary": "The SEC approval of ETH ETFs brings positive sentiment to the market.",
            "link": "https://example.com/2",
            "published": datetime.datetime.now() - datetime.timedelta(hours=5),
            "source": "https://cointelegraph.com/rss",
        },
        {
            "title": "Solana Network Upgrade Promises Faster Transactions",
            "summary": "Solana announces a major upgrade that could boost network performance.",
            "link": "https://example.com/3",
            "published": datetime.datetime.now() - datetime.timedelta(hours=8),
            "source": "https://decrypt.co/feed",
        },
        {
            "title": "Crypto Market Faces Regulatory Concerns",
            "summary": "New SEC regulations raise fear and uncertainty in the crypto market.",
            "link": "https://example.com/4",
            "published": datetime.datetime.now() - datetime.timedelta(hours=12),
            "source": "https://coindesk.com/rss",
        },
        {
            "title": "Bitcoin Mining Difficulty Reaches New Record",
            "summary": "Mining difficulty adjustment shows network strength.",
            "link": "https://example.com/5",
            "published": datetime.datetime.now() - datetime.timedelta(hours=1),
            "source": "https://cointelegraph.com/rss",
        },
    ]


@pytest.fixture
def mock_coingecko_response() -> dict[str, Any]:
    return {
        "bitcoin": {
            "usd": 65432.10,
            "usd_market_cap": 1280000000000,
            "usd_24h_vol": 28500000000,
            "usd_24h_change": 2.35,
        }
    }


@pytest.fixture
def mock_market_chart_response() -> dict[str, Any]:
    import math

    base = 65000.0
    prices = [
        [1700000000000 + i * 3600000, base + 500 * math.sin(i / 10)]
        for i in range(336)
    ]
    return {"prices": prices}


@pytest.fixture
def mock_search_response() -> dict[str, Any]:
    return {
        "coins": [
            {"id": "bitcoin", "name": "Bitcoin", "symbol": "btc"},
            {"id": "bitcoin-cash", "name": "Bitcoin Cash", "symbol": "bch"},
        ]
    }


@pytest.fixture
def mock_discord_bot() -> MagicMock:
    bot = MagicMock()
    bot.fetch_user = AsyncMock()
    return bot
