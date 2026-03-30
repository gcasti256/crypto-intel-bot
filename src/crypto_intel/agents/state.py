from __future__ import annotations

from typing import TypedDict


class AnalysisState(TypedDict, total=False):
    token: str
    token_id: str
    price_data: dict
    price_history: list[dict]
    technical_indicators: dict
    news_articles: list[dict]
    sentiment_score: float
    relevant_context: list[str]
    analysis_summary: str
    risk_level: str
    confidence: float
