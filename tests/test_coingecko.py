from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import httpx
import pytest

from crypto_intel.data.coingecko import CoinGeckoClient


@pytest.fixture
def client():
    c = CoinGeckoClient("https://api.coingecko.com/api/v3")
    c._min_interval = 0  # disable rate limiting in tests
    return c


class TestTokenResolution:
    def test_resolve_known_symbol(self, client):
        assert client.resolve_token("btc") == "bitcoin"
        assert client.resolve_token("ETH") == "ethereum"
        assert client.resolve_token("sol") == "solana"

    def test_resolve_unknown_falls_through(self, client):
        assert client.resolve_token("unknowntoken") == "unknowntoken"

    @pytest.mark.asyncio
    async def test_search_token_known(self, client):
        result = await client.search_token("btc")
        assert result == "bitcoin"

    @pytest.mark.asyncio
    async def test_search_token_api(self, client, mock_search_response):
        mock_resp = MagicMock()
        mock_resp.json.return_value = mock_search_response
        mock_resp.raise_for_status = MagicMock()

        client._client = AsyncMock()
        client._client.get = AsyncMock(return_value=mock_resp)

        result = await client.search_token("something_unknown_xyz")
        assert result == "bitcoin"


class TestGetPrice:
    @pytest.mark.asyncio
    async def test_get_price(self, client, mock_coingecko_response):
        mock_resp = MagicMock()
        mock_resp.json.return_value = mock_coingecko_response
        mock_resp.raise_for_status = MagicMock()

        client._client = AsyncMock()
        client._client.get = AsyncMock(return_value=mock_resp)

        result = await client.get_price("bitcoin")
        assert result["price"] == 65432.10
        assert result["market_cap"] == 1_280_000_000_000
        assert result["volume_24h"] == 28_500_000_000
        assert result["change_24h"] == 2.35

    @pytest.mark.asyncio
    async def test_get_price_caching(self, client, mock_coingecko_response):
        mock_resp = MagicMock()
        mock_resp.json.return_value = mock_coingecko_response
        mock_resp.raise_for_status = MagicMock()

        client._client = AsyncMock()
        client._client.get = AsyncMock(return_value=mock_resp)

        result1 = await client.get_price("bitcoin")
        result2 = await client.get_price("bitcoin")

        assert result1 == result2
        assert client._client.get.call_count == 1


class TestGetMarketChart:
    @pytest.mark.asyncio
    async def test_get_market_chart(self, client, mock_market_chart_response):
        mock_resp = MagicMock()
        mock_resp.json.return_value = mock_market_chart_response
        mock_resp.raise_for_status = MagicMock()

        client._client = AsyncMock()
        client._client.get = AsyncMock(return_value=mock_resp)

        result = await client.get_market_chart("bitcoin", days=14)
        assert len(result) == 336
        assert "timestamp" in result[0]
        assert "price" in result[0]


class TestErrorHandling:
    @pytest.mark.asyncio
    async def test_http_error(self, client):
        client._client = AsyncMock()
        client._client.get = AsyncMock(
            side_effect=httpx.HTTPStatusError(
                "Not Found",
                request=MagicMock(),
                response=MagicMock(status_code=404),
            )
        )

        with pytest.raises(httpx.HTTPStatusError):
            await client.get_price("invalid_token_xyz")
