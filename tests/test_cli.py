from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from crypto_intel.cli import cli


@pytest.fixture
def runner():
    return CliRunner()


class TestCLI:
    def test_help(self, runner):
        result = runner.invoke(cli, ["--help"])
        assert result.exit_code == 0
        assert "Crypto Intel Bot" in result.output

    def test_run_no_token(self, runner):
        with patch("crypto_intel.cli.get_settings") as mock_settings:
            mock_settings.return_value = MagicMock(discord_token="")
            result = runner.invoke(cli, ["run"])
            assert result.exit_code == 1

    def test_init_db(self, runner):
        with patch("crypto_intel.cli.get_settings") as mock_settings:
            mock_settings.return_value = MagicMock(
                database_url="sqlite+aiosqlite:///:memory:"
            )
            result = runner.invoke(cli, ["init-db"])
            assert result.exit_code == 0
            assert "initialized" in result.output.lower()

    def test_alerts_list(self, runner):
        with patch("crypto_intel.cli.get_settings") as mock_settings:
            mock_settings.return_value = MagicMock(
                database_url="sqlite+aiosqlite:///:memory:"
            )
            result = runner.invoke(cli, ["alerts", "list"])
            assert result.exit_code == 0
