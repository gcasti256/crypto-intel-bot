from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from crypto_intel.alerts.models import PriceAlert
from crypto_intel.alerts.monitor import AlertMonitor


class TestPriceAlert:
    def test_create_alert(self):
        alert = PriceAlert(
            user_id="123",
            token="btc",
            condition="above",
            threshold=70000.0,
        )
        assert alert.active is True
        assert alert.triggered_at is None

    def test_check_above_triggered(self):
        alert = PriceAlert(
            user_id="123", token="btc", condition="above", threshold=70000.0
        )
        assert alert.check(75000.0) is True

    def test_check_above_not_triggered(self):
        alert = PriceAlert(
            user_id="123", token="btc", condition="above", threshold=70000.0
        )
        assert alert.check(65000.0) is False

    def test_check_below_triggered(self):
        alert = PriceAlert(
            user_id="123", token="btc", condition="below", threshold=60000.0
        )
        assert alert.check(55000.0) is True

    def test_check_below_not_triggered(self):
        alert = PriceAlert(
            user_id="123", token="btc", condition="below", threshold=60000.0
        )
        assert alert.check(65000.0) is False

    def test_check_inactive_alert(self):
        alert = PriceAlert(
            user_id="123", token="btc", condition="above", threshold=70000.0, active=False
        )
        assert alert.check(75000.0) is False

    def test_check_exact_threshold_above(self):
        alert = PriceAlert(
            user_id="123", token="btc", condition="above", threshold=70000.0
        )
        assert alert.check(70000.0) is True

    def test_check_exact_threshold_below(self):
        alert = PriceAlert(
            user_id="123", token="btc", condition="below", threshold=60000.0
        )
        assert alert.check(60000.0) is True


class TestAlertMonitor:
    @pytest.fixture
    def mock_db(self):
        db = MagicMock()
        session = AsyncMock()
        session.__aenter__ = AsyncMock(return_value=session)
        session.__aexit__ = AsyncMock(return_value=None)
        db.get_session = AsyncMock(return_value=session)
        return db

    @pytest.fixture
    def mock_coingecko(self):
        cg = MagicMock()
        cg.resolve_token.return_value = "bitcoin"
        cg.get_price = AsyncMock(return_value={"price": 72000.0})
        return cg

    def test_monitor_creation(self, mock_db, mock_coingecko):
        monitor = AlertMonitor(
            db=mock_db, coingecko=mock_coingecko, interval=30
        )
        assert monitor.interval == 30
        assert monitor._running is False

    def test_stop(self, mock_db, mock_coingecko):
        monitor = AlertMonitor(db=mock_db, coingecko=mock_coingecko)
        monitor._running = True
        monitor.stop()
        assert monitor._running is False
