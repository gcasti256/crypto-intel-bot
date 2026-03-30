from __future__ import annotations

import structlog

from crypto_intel.agents.state import AnalysisState
from crypto_intel.llm.provider import LLMProvider

log = structlog.get_logger()

_llm_provider: LLMProvider | None = None


def set_llm_provider(provider: LLMProvider | None) -> None:
    global _llm_provider
    _llm_provider = provider


def _determine_risk_level(state: AnalysisState) -> tuple[str, float]:
    indicators = state.get("technical_indicators", {})
    sentiment = state.get("sentiment_score", 0.0)
    signal = indicators.get("signal", "neutral")
    rsi = indicators.get("rsi", 50.0)

    risk_score = 0.5

    if signal == "bearish":
        risk_score += 0.2
    elif signal == "bullish":
        risk_score -= 0.1

    if sentiment < -0.3:
        risk_score += 0.15
    elif sentiment > 0.3:
        risk_score -= 0.1

    if rsi > 80:
        risk_score += 0.15
    elif rsi < 20:
        risk_score += 0.1

    risk_score = max(0.0, min(1.0, risk_score))

    if risk_score >= 0.65:
        return "high", 1.0 - risk_score
    elif risk_score >= 0.4:
        return "medium", 0.6
    else:
        return "low", 0.8


def _format_number(n: float) -> str:
    if abs(n) >= 1_000_000_000:
        return f"${n / 1_000_000_000:.2f}B"
    elif abs(n) >= 1_000_000:
        return f"${n / 1_000_000:.2f}M"
    elif abs(n) >= 1_000:
        return f"${n:,.0f}"
    elif abs(n) >= 1:
        return f"${n:,.2f}"
    else:
        return f"${n:.6f}"


def _generate_template_summary(state: AnalysisState) -> str:
    token = state.get("token", "").upper()
    price_data = state.get("price_data", {})
    indicators = state.get("technical_indicators", {})
    sentiment = state.get("sentiment_score", 0.0)

    price = price_data.get("price", 0)
    change = price_data.get("change_24h", 0)
    signal = indicators.get("signal", "neutral")
    rsi = indicators.get("rsi", 50)

    trend = "upward" if change > 0 else "downward"
    sent_label = "positive" if sentiment > 0.1 else "negative" if sentiment < -0.1 else "neutral"

    return (
        f"{token} is trading at {_format_number(price)} with a {abs(change):.1f}% "
        f"{'gain' if change > 0 else 'loss'} over 24h. "
        f"Technical analysis shows a {signal} signal with RSI at {rsi:.0f}, "
        f"indicating {'overbought conditions' if rsi > 70 else 'oversold conditions' if rsi < 30 else 'normal momentum'}. "
        f"News sentiment is {sent_label} ({sentiment:+.2f}). "
        f"Overall trend is {trend} with {signal} technical bias."
    )


async def report_agent(state: AnalysisState) -> AnalysisState:
    log.info("agent.report", token=state.get("token"))

    risk_level, confidence = _determine_risk_level(state)

    existing_summary = state.get("analysis_summary", "")

    if _llm_provider and not existing_summary:
        try:
            prompt = _build_llm_prompt(state)
            existing_summary = await _llm_provider.generate(
                prompt, system="You are a professional crypto market analyst."
            )
        except Exception:
            log.warning("agent.report.llm_failed")

    if not existing_summary:
        existing_summary = _generate_template_summary(state)

    return {
        "analysis_summary": existing_summary,
        "risk_level": risk_level,
        "confidence": confidence,
    }


def _build_llm_prompt(state: AnalysisState) -> str:
    token = state.get("token", "").upper()
    price_data = state.get("price_data", {})
    indicators = state.get("technical_indicators", {})
    sentiment = state.get("sentiment_score", 0.0)

    return (
        f"Generate a concise market analysis for {token}.\n\n"
        f"Price: ${price_data.get('price', 0):,.2f}\n"
        f"24h Change: {price_data.get('change_24h', 0):.1f}%\n"
        f"Market Cap: {_format_number(price_data.get('market_cap', 0))}\n"
        f"RSI: {indicators.get('rsi', 50):.0f}\n"
        f"Technical Signal: {indicators.get('signal', 'neutral')}\n"
        f"Sentiment Score: {sentiment:+.2f}\n\n"
        f"Provide a 3-sentence analysis covering price action, technicals, and sentiment."
    )
