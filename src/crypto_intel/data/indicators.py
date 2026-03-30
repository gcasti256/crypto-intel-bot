from __future__ import annotations

import numpy as np


def compute_sma(prices: list[float], period: int) -> list[float]:
    if len(prices) < period:
        return []
    arr = np.array(prices, dtype=np.float64)
    kernel = np.ones(period) / period
    sma = np.convolve(arr, kernel, mode="valid")
    return sma.tolist()


def compute_ema(prices: list[float], period: int) -> list[float]:
    if len(prices) < period:
        return []
    arr = np.array(prices, dtype=np.float64)
    multiplier = 2.0 / (period + 1)
    ema_values = [float(np.mean(arr[:period]))]
    for i in range(period, len(arr)):
        ema_values.append(arr[i] * multiplier + ema_values[-1] * (1 - multiplier))
    return ema_values


def compute_rsi(prices: list[float], period: int = 14) -> float:
    if len(prices) < period + 1:
        return 50.0

    arr = np.array(prices, dtype=np.float64)
    deltas = np.diff(arr)

    gains = np.where(deltas > 0, deltas, 0.0)
    losses = np.where(deltas < 0, -deltas, 0.0)

    avg_gain = float(np.mean(gains[:period]))
    avg_loss = float(np.mean(losses[:period]))

    for i in range(period, len(deltas)):
        avg_gain = (avg_gain * (period - 1) + gains[i]) / period
        avg_loss = (avg_loss * (period - 1) + losses[i]) / period

    if avg_loss == 0:
        return 100.0 if avg_gain > 0 else 50.0

    rs = avg_gain / avg_loss
    return 100.0 - (100.0 / (1.0 + rs))


def compute_macd(
    prices: list[float],
    fast: int = 12,
    slow: int = 26,
    signal_period: int = 9,
) -> tuple[list[float], list[float], list[float]]:
    if len(prices) < slow + signal_period:
        return [], [], []

    fast_ema = compute_ema(prices, fast)
    slow_ema = compute_ema(prices, slow)

    offset = len(fast_ema) - len(slow_ema)
    macd_line = [f - s for f, s in zip(fast_ema[offset:], slow_ema)]

    if len(macd_line) < signal_period:
        return macd_line, [], []

    signal_line = compute_ema(macd_line, signal_period)

    hist_offset = len(macd_line) - len(signal_line)
    histogram = [m - s for m, s in zip(macd_line[hist_offset:], signal_line)]

    return macd_line, signal_line, histogram


def compute_bollinger_bands(
    prices: list[float], period: int = 20, std_dev: float = 2.0
) -> tuple[list[float], list[float], list[float]]:
    if len(prices) < period:
        return [], [], []

    arr = np.array(prices, dtype=np.float64)
    upper, middle, lower = [], [], []

    for i in range(period - 1, len(arr)):
        window = arr[i - period + 1 : i + 1]
        mean = float(np.mean(window))
        std = float(np.std(window, ddof=0))
        middle.append(mean)
        upper.append(mean + std_dev * std)
        lower.append(mean - std_dev * std)

    return upper, middle, lower


def technical_signal(indicators: dict) -> str:
    signals: list[int] = []

    rsi = indicators.get("rsi")
    if rsi is not None:
        if rsi < 30:
            signals.append(1)  # oversold = bullish
        elif rsi > 70:
            signals.append(-1)  # overbought = bearish
        else:
            signals.append(0)

    macd_histogram = indicators.get("macd_histogram")
    if macd_histogram and len(macd_histogram) > 0:
        if macd_histogram[-1] > 0:
            signals.append(1)
        elif macd_histogram[-1] < 0:
            signals.append(-1)
        else:
            signals.append(0)

    price = indicators.get("current_price")
    sma_50 = indicators.get("sma_50")
    if price is not None and sma_50 and len(sma_50) > 0:
        if price > sma_50[-1]:
            signals.append(1)
        else:
            signals.append(-1)

    bb_upper = indicators.get("bb_upper")
    bb_lower = indicators.get("bb_lower")
    if price is not None and bb_upper and bb_lower and len(bb_upper) > 0:
        if price >= bb_upper[-1]:
            signals.append(-1)  # near upper band = bearish
        elif price <= bb_lower[-1]:
            signals.append(1)  # near lower band = bullish
        else:
            signals.append(0)

    if not signals:
        return "neutral"

    avg = sum(signals) / len(signals)
    if avg > 0.25:
        return "bullish"
    elif avg < -0.25:
        return "bearish"
    return "neutral"
