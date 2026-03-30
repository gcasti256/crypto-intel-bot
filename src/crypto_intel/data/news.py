from __future__ import annotations

import datetime
from typing import Any

import feedparser
import httpx
import structlog

log = structlog.get_logger()

RSS_FEEDS = [
    "https://www.coindesk.com/arc/outboundfeeds/rss/",
    "https://cointelegraph.com/rss",
    "https://decrypt.co/feed",
]


class NewsFetcher:
    def __init__(self, feeds: list[str] | None = None) -> None:
        self.feeds = feeds or RSS_FEEDS
        self._client = httpx.AsyncClient(timeout=15.0)

    async def close(self) -> None:
        await self._client.aclose()

    async def fetch_feed(self, url: str) -> list[dict[str, Any]]:
        try:
            resp = await self._client.get(url, follow_redirects=True)
            resp.raise_for_status()
            feed = feedparser.parse(resp.text)
            articles = []
            for entry in feed.entries:
                published = None
                if hasattr(entry, "published_parsed") and entry.published_parsed:
                    published = datetime.datetime(*entry.published_parsed[:6])

                articles.append({
                    "title": entry.get("title", ""),
                    "summary": entry.get("summary", ""),
                    "link": entry.get("link", ""),
                    "published": published,
                    "source": url,
                })
            return articles
        except (httpx.HTTPError, Exception) as e:
            log.warning("news.fetch_failed", url=url, error=str(e))
            return []

    async def fetch_all(self, max_age_hours: int = 48) -> list[dict[str, Any]]:
        all_articles: list[dict[str, Any]] = []
        for feed_url in self.feeds:
            articles = await self.fetch_feed(feed_url)
            all_articles.extend(articles)

        cutoff = datetime.datetime.now() - datetime.timedelta(hours=max_age_hours)
        filtered = []
        for article in all_articles:
            pub = article.get("published")
            if pub is None or pub >= cutoff:
                filtered.append(article)

        return filtered

    @staticmethod
    def filter_by_token(
        articles: list[dict[str, Any]], token: str
    ) -> list[dict[str, Any]]:
        keywords = {token.lower()}
        expanded = {
            "btc": {"bitcoin", "btc"},
            "eth": {"ethereum", "eth", "ether"},
            "sol": {"solana", "sol"},
            "bnb": {"binance", "bnb"},
            "xrp": {"ripple", "xrp"},
            "ada": {"cardano", "ada"},
            "doge": {"dogecoin", "doge"},
            "dot": {"polkadot", "dot"},
            "avax": {"avalanche", "avax"},
            "link": {"chainlink", "link"},
        }
        keywords.update(expanded.get(token.lower(), set()))

        matching = []
        for article in articles:
            text = f"{article.get('title', '')} {article.get('summary', '')}".lower()
            if any(kw in text for kw in keywords):
                matching.append(article)

        return matching
