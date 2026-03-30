from __future__ import annotations

from typing import Any

import structlog

from crypto_intel.agents.state import AnalysisState
from crypto_intel.data.news import NewsFetcher
from crypto_intel.llm.provider import LLMProvider
from crypto_intel.rag.retriever import Retriever

log = structlog.get_logger()

POSITIVE_WORDS = {
    "bullish", "surge", "rally", "gain", "soar", "breakout", "moon", "pump",
    "adoption", "partnership", "launch", "upgrade", "milestone", "record",
    "growth", "profit", "positive", "optimistic", "recovery", "innovation",
    "institutional", "accumulation", "mainstream", "approval", "etf",
}

NEGATIVE_WORDS = {
    "bearish", "crash", "dump", "plunge", "sell-off", "selloff", "hack",
    "exploit", "scam", "fraud", "ban", "regulation", "sec", "lawsuit",
    "decline", "loss", "negative", "pessimistic", "fear", "bankruptcy",
    "liquidation", "rug", "rugpull", "collapse", "warning", "risk",
}

_news_fetcher: NewsFetcher | None = None
_llm_provider: LLMProvider | None = None
_retriever: Retriever | None = None


def configure(
    news_fetcher: NewsFetcher | None = None,
    llm_provider: LLMProvider | None = None,
    retriever: Retriever | None = None,
) -> None:
    global _news_fetcher, _llm_provider, _retriever
    _news_fetcher = news_fetcher
    _llm_provider = llm_provider
    _retriever = retriever


def compute_keyword_sentiment(articles: list[dict[str, Any]]) -> float:
    if not articles:
        return 0.0

    total_score = 0.0
    for article in articles:
        text = f"{article.get('title', '')} {article.get('summary', '')}".lower()
        pos = sum(1 for w in POSITIVE_WORDS if w in text)
        neg = sum(1 for w in NEGATIVE_WORDS if w in text)
        total = pos + neg
        if total > 0:
            total_score += (pos - neg) / total

    return max(-1.0, min(1.0, total_score / max(len(articles), 1)))


async def sentiment_agent(state: AnalysisState) -> AnalysisState:
    token = state["token"]
    log.info("agent.sentiment", token=token)

    news_fetcher = _news_fetcher or NewsFetcher()
    retriever = _retriever or Retriever()

    articles = state.get("news_articles", [])
    if not articles:
        try:
            all_articles = await news_fetcher.fetch_all()
            articles = NewsFetcher.filter_by_token(all_articles, token)
        except Exception:
            log.warning("agent.sentiment.fetch_failed", token=token)
            articles = []

    retriever.add_articles(articles)
    relevant = retriever.retrieve(f"{token} price analysis market", k=5)

    sentiment = compute_keyword_sentiment(articles)

    summary = ""
    if _llm_provider and articles:
        try:
            headlines = "\n".join(
                f"- {a.get('title', 'No title')}" for a in articles[:10]
            )
            prompt = (
                f"Analyze the sentiment for {token.upper()} based on these headlines:\n"
                f"{headlines}\n\n"
                f"Current sentiment score: {sentiment:.2f} (-1 bearish to +1 bullish)\n"
                f"Provide a brief 2-sentence sentiment summary."
            )
            summary = await _llm_provider.generate(
                prompt, system="You are a crypto market analyst."
            )
        except Exception:
            log.warning("agent.sentiment.llm_failed")

    return {
        "news_articles": articles,
        "sentiment_score": sentiment,
        "relevant_context": relevant,
        "analysis_summary": summary,
    }
