from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from crypto_intel.data.news import NewsFetcher

SAMPLE_RSS = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
<channel>
<title>Crypto News</title>
<item>
<title>Bitcoin Hits New High</title>
<description>BTC reaches a new all-time high as adoption grows.</description>
<link>https://example.com/btc-high</link>
<pubDate>Mon, 30 Mar 2026 10:00:00 GMT</pubDate>
</item>
<item>
<title>Ethereum Upgrade Complete</title>
<description>The latest Ethereum upgrade improves scalability.</description>
<link>https://example.com/eth-upgrade</link>
<pubDate>Mon, 30 Mar 2026 08:00:00 GMT</pubDate>
</item>
</channel>
</rss>"""


@pytest.fixture
def fetcher():
    return NewsFetcher(feeds=["https://example.com/rss"])


class TestFetchFeed:
    @pytest.mark.asyncio
    async def test_parse_rss(self, fetcher):
        mock_resp = MagicMock()
        mock_resp.text = SAMPLE_RSS
        mock_resp.raise_for_status = MagicMock()

        fetcher._client = AsyncMock()
        fetcher._client.get = AsyncMock(return_value=mock_resp)

        articles = await fetcher.fetch_feed("https://example.com/rss")
        assert len(articles) == 2
        assert articles[0]["title"] == "Bitcoin Hits New High"
        assert "example.com" in articles[0]["link"]

    @pytest.mark.asyncio
    async def test_fetch_failed_returns_empty(self, fetcher):
        fetcher._client = AsyncMock()
        fetcher._client.get = AsyncMock(side_effect=Exception("Network error"))

        articles = await fetcher.fetch_feed("https://broken.example.com")
        assert articles == []


class TestFilterByToken:
    def test_filter_btc(self, sample_articles):
        result = NewsFetcher.filter_by_token(sample_articles, "btc")
        assert len(result) >= 2
        assert any("Bitcoin" in a["title"] for a in result)

    def test_filter_eth(self, sample_articles):
        result = NewsFetcher.filter_by_token(sample_articles, "eth")
        assert len(result) >= 1

    def test_filter_nonexistent(self, sample_articles):
        result = NewsFetcher.filter_by_token(sample_articles, "zzz_fake_token")
        assert len(result) == 0

    def test_filter_empty_articles(self):
        result = NewsFetcher.filter_by_token([], "btc")
        assert result == []
