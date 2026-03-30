from __future__ import annotations

import structlog

from crypto_intel.agents.state import AnalysisState
from crypto_intel.data.indicators import (
    compute_bollinger_bands,
    compute_ema,
    compute_macd,
    compute_rsi,
    compute_sma,
    technical_signal,
)

log = structlog.get_logger()


async def technical_agent(state: AnalysisState) -> AnalysisState:
    price_history = state.get("price_history", [])
    prices = [p["price"] for p in price_history]

    log.info("agent.technical", num_prices=len(prices))

    if len(prices) < 30:
        return {
            "technical_indicators": {
                "rsi": 50.0,
                "macd_line": [],
                "signal_line": [],
                "macd_histogram": [],
                "bb_upper": [],
                "bb_middle": [],
                "bb_lower": [],
                "sma_7": [],
                "sma_25": [],
                "sma_50": [],
                "ema_12": [],
                "ema_26": [],
                "signal": "neutral",
                "current_price": prices[-1] if prices else 0,
            },
        }

    rsi = compute_rsi(prices)
    macd_line, signal_line, histogram = compute_macd(prices)
    bb_upper, bb_middle, bb_lower = compute_bollinger_bands(prices)
    sma_7 = compute_sma(prices, 7)
    sma_25 = compute_sma(prices, 25)
    sma_50 = compute_sma(prices, 50)
    ema_12 = compute_ema(prices, 12)
    ema_26 = compute_ema(prices, 26)

    indicators = {
        "rsi": rsi,
        "macd_line": macd_line,
        "signal_line": signal_line,
        "macd_histogram": histogram,
        "bb_upper": bb_upper,
        "bb_middle": bb_middle,
        "bb_lower": bb_lower,
        "sma_7": sma_7,
        "sma_25": sma_25,
        "sma_50": sma_50,
        "ema_12": ema_12,
        "ema_26": ema_26,
        "current_price": prices[-1],
        "signal": technical_signal({
            "rsi": rsi,
            "macd_histogram": histogram,
            "sma_50": sma_50,
            "bb_upper": bb_upper,
            "bb_lower": bb_lower,
            "current_price": prices[-1],
        }),
    }

    return {"technical_indicators": indicators}
