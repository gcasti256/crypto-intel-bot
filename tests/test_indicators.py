from __future__ import annotations

import numpy as np

from crypto_intel.data.indicators import (
    compute_bollinger_bands,
    compute_ema,
    compute_macd,
    compute_rsi,
    compute_sma,
    technical_signal,
)


class TestSMA:
    def test_basic_sma(self):
        prices = [10.0, 20.0, 30.0, 40.0, 50.0]
        result = compute_sma(prices, 3)
        assert len(result) == 3
        assert abs(result[0] - 20.0) < 1e-10
        assert abs(result[1] - 30.0) < 1e-10
        assert abs(result[2] - 40.0) < 1e-10

    def test_sma_single_period(self):
        prices = [1.0, 2.0, 3.0]
        result = compute_sma(prices, 1)
        assert len(result) == 3
        for i, p in enumerate(prices):
            assert abs(result[i] - p) < 1e-10

    def test_sma_full_period(self):
        prices = [10.0, 20.0, 30.0]
        result = compute_sma(prices, 3)
        assert len(result) == 1
        assert abs(result[0] - 20.0) < 1e-10

    def test_sma_insufficient_data(self):
        prices = [10.0, 20.0]
        result = compute_sma(prices, 5)
        assert result == []

    def test_sma_flat_prices(self):
        prices = [100.0] * 20
        result = compute_sma(prices, 5)
        for v in result:
            assert abs(v - 100.0) < 1e-10


class TestEMA:
    def test_basic_ema(self):
        prices = [22.0, 22.5, 22.3, 22.8, 23.0, 23.2, 23.5, 23.1, 23.4, 23.6]
        result = compute_ema(prices, 5)
        assert len(result) > 0
        assert abs(result[0] - np.mean(prices[:5])) < 1e-10

    def test_ema_insufficient_data(self):
        prices = [10.0, 20.0]
        result = compute_ema(prices, 5)
        assert result == []

    def test_ema_trending_up(self):
        prices = list(range(1, 21))
        prices = [float(p) for p in prices]
        result = compute_ema(prices, 5)
        for i in range(1, len(result)):
            assert result[i] > result[i - 1]


class TestRSI:
    def test_rsi_known_values(self):
        gains = [1.0] * 14
        losses = [-0.5] * 14
        prices = [100.0]
        for gain, loss in zip(gains, losses):
            prices.append(prices[-1] + gain)
            prices.append(prices[-1] + loss)
        rsi = compute_rsi(prices, 14)
        assert 0.0 <= rsi <= 100.0

    def test_rsi_all_gains(self):
        prices = [float(i) for i in range(1, 30)]
        rsi = compute_rsi(prices, 14)
        assert rsi == 100.0

    def test_rsi_all_losses(self):
        prices = [float(30 - i) for i in range(30)]
        rsi = compute_rsi(prices, 14)
        assert rsi < 5.0

    def test_rsi_insufficient_data(self):
        prices = [100.0, 101.0]
        rsi = compute_rsi(prices, 14)
        assert rsi == 50.0  # default

    def test_rsi_range(self, sample_prices):
        rsi = compute_rsi(sample_prices)
        assert 0.0 <= rsi <= 100.0

    def test_rsi_flat_prices(self):
        prices = [100.0] * 30
        rsi = compute_rsi(prices, 14)
        assert rsi == 50.0  # no movement = default


class TestMACD:
    def test_macd_basic(self, sample_prices):
        macd_line, signal_line, histogram = compute_macd(sample_prices)
        assert len(macd_line) > 0
        assert len(signal_line) > 0
        assert len(histogram) > 0

    def test_macd_histogram_matches(self, sample_prices):
        macd_line, signal_line, histogram = compute_macd(sample_prices)
        offset = len(macd_line) - len(signal_line)
        for i, h in enumerate(histogram):
            expected = macd_line[offset + i] - signal_line[i]
            assert abs(h - expected) < 1e-10

    def test_macd_insufficient_data(self):
        prices = [100.0] * 10
        macd_line, signal_line, histogram = compute_macd(prices)
        assert macd_line == []

    def test_macd_trending(self):
        prices = [float(i) for i in range(50)]
        macd_line, signal_line, histogram = compute_macd(prices)
        assert len(macd_line) > 0
        assert macd_line[-1] > 0  # bullish crossover in uptrend


class TestBollingerBands:
    def test_basic_bands(self, sample_prices):
        upper, middle, lower = compute_bollinger_bands(sample_prices[:30])
        assert len(upper) > 0
        assert len(middle) > 0
        assert len(lower) > 0

    def test_upper_above_lower(self, sample_prices):
        upper, middle, lower = compute_bollinger_bands(sample_prices)
        for u, m, lo in zip(upper, middle, lower):
            assert u >= m >= lo

    def test_flat_prices_narrow_bands(self):
        prices = [100.0] * 25
        upper, middle, lower = compute_bollinger_bands(prices)
        for u, m, lo in zip(upper, middle, lower):
            assert abs(u - m) < 1e-10
            assert abs(m - lo) < 1e-10

    def test_insufficient_data(self):
        prices = [100.0] * 5
        upper, middle, lower = compute_bollinger_bands(prices)
        assert upper == []


class TestTechnicalSignal:
    def test_bullish_signal(self):
        indicators = {
            "rsi": 25.0,
            "macd_histogram": [0.5],
            "sma_50": [60000.0],
            "bb_upper": [67000.0],
            "bb_lower": [63000.0],
            "current_price": 65500.0,
        }
        assert technical_signal(indicators) == "bullish"

    def test_bearish_signal(self):
        indicators = {
            "rsi": 75.0,
            "macd_histogram": [-0.5],
            "sma_50": [66000.0],
            "bb_upper": [65500.0],
            "bb_lower": [63000.0],
            "current_price": 65500.0,
        }
        assert technical_signal(indicators) == "bearish"

    def test_neutral_signal(self):
        indicators = {
            "rsi": 50.0,
            "macd_histogram": [0.01],
            "sma_50": [65000.0],
            "bb_upper": [67000.0],
            "bb_lower": [63000.0],
            "current_price": 65000.0,
        }
        result = technical_signal(indicators)
        assert result in ("bullish", "neutral")

    def test_empty_indicators(self):
        assert technical_signal({}) == "neutral"
