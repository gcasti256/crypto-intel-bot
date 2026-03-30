from __future__ import annotations

import asyncio
import time
from typing import Any

import httpx
import structlog

log = structlog.get_logger()

SYMBOL_MAP: dict[str, str] = {
    "btc": "bitcoin",
    "eth": "ethereum",
    "sol": "solana",
    "bnb": "binancecoin",
    "xrp": "ripple",
    "ada": "cardano",
    "doge": "dogecoin",
    "dot": "polkadot",
    "matic": "matic-network",
    "avax": "avalanche-2",
    "link": "chainlink",
    "uni": "uniswap",
    "atom": "cosmos",
    "ltc": "litecoin",
    "near": "near",
    "apt": "aptos",
    "arb": "arbitrum",
    "op": "optimism",
    "sui": "sui",
    "pepe": "pepe",
}

FEAR_GREED_URL = "https://api.alternative.me/fng/"


class CoinGeckoClient:
    def __init__(self, base_url: str = "https://api.coingecko.com/api/v3") -> None:
        self.base_url = base_url.rstrip("/")
        self._client = httpx.AsyncClient(timeout=15.0)
        self._cache: dict[str, tuple[float, Any]] = {}
        self._rate_limit = asyncio.Semaphore(10)
        self._last_request = 0.0
        self._min_interval = 6.0  # 10 req/min = 1 per 6 seconds

    async def close(self) -> None:
        await self._client.aclose()

    def _cache_get(self, key: str, ttl: float) -> Any | None:
        if key in self._cache:
            ts, data = self._cache[key]
            if time.monotonic() - ts < ttl:
                return data
            del self._cache[key]
        return None

    def _cache_set(self, key: str, data: Any) -> None:
        self._cache[key] = (time.monotonic(), data)

    async def _get(self, path: str, params: dict[str, Any] | None = None) -> Any:
        async with self._rate_limit:
            now = time.monotonic()
            wait = self._min_interval - (now - self._last_request)
            if wait > 0:
                await asyncio.sleep(wait)

            url = f"{self.base_url}{path}"
            log.debug("coingecko.request", path=path, params=params)
            resp = await self._client.get(url, params=params)
            self._last_request = time.monotonic()
            resp.raise_for_status()
            return resp.json()

    def resolve_token(self, symbol: str) -> str:
        sym = symbol.lower().strip()
        return SYMBOL_MAP.get(sym, sym)

    async def search_token(self, query: str) -> str | None:
        sym = query.lower().strip()
        if sym in SYMBOL_MAP:
            return SYMBOL_MAP[sym]

        cache_key = f"search:{sym}"
        cached = self._cache_get(cache_key, ttl=300)
        if cached is not None:
            return cached

        try:
            data = await self._get("/search", params={"query": sym})
            coins = data.get("coins", [])
            if coins:
                result = coins[0]["id"]
                self._cache_set(cache_key, result)
                return result
        except httpx.HTTPError:
            log.warning("coingecko.search_failed", query=query)

        return None

    async def get_price(self, token_id: str) -> dict[str, Any]:
        cache_key = f"price:{token_id}"
        cached = self._cache_get(cache_key, ttl=60)
        if cached is not None:
            return cached

        data = await self._get(
            "/simple/price",
            params={
                "ids": token_id,
                "vs_currencies": "usd",
                "include_market_cap": "true",
                "include_24hr_vol": "true",
                "include_24hr_change": "true",
            },
        )

        token_data = data.get(token_id, {})
        result = {
            "price": token_data.get("usd", 0),
            "market_cap": token_data.get("usd_market_cap", 0),
            "volume_24h": token_data.get("usd_24h_vol", 0),
            "change_24h": token_data.get("usd_24h_change", 0),
        }
        self._cache_set(cache_key, result)
        return result

    async def get_market_chart(
        self, token_id: str, days: int = 14
    ) -> list[dict[str, float]]:
        cache_key = f"chart:{token_id}:{days}"
        cached = self._cache_get(cache_key, ttl=300)
        if cached is not None:
            return cached

        data = await self._get(
            f"/coins/{token_id}/market_chart",
            params={"vs_currency": "usd", "days": str(days)},
        )

        prices = data.get("prices", [])
        result = [
            {"timestamp": p[0], "price": p[1]}
            for p in prices
        ]
        self._cache_set(cache_key, result)
        return result

    async def get_top_gainers_losers(
        self, limit: int = 5
    ) -> dict[str, list[dict[str, Any]]]:
        cache_key = f"market:gainers_losers:{limit}"
        cached = self._cache_get(cache_key, ttl=120)
        if cached is not None:
            return cached

        data = await self._get(
            "/coins/markets",
            params={
                "vs_currency": "usd",
                "order": "market_cap_desc",
                "per_page": "100",
                "page": "1",
                "sparkline": "false",
                "price_change_percentage": "24h",
            },
        )

        sorted_by_change = sorted(
            data, key=lambda x: x.get("price_change_percentage_24h") or 0
        )

        losers = [
            {
                "name": c["name"],
                "symbol": c["symbol"].upper(),
                "price": c.get("current_price", 0),
                "change_24h": c.get("price_change_percentage_24h", 0),
            }
            for c in sorted_by_change[:limit]
        ]

        gainers = [
            {
                "name": c["name"],
                "symbol": c["symbol"].upper(),
                "price": c.get("current_price", 0),
                "change_24h": c.get("price_change_percentage_24h", 0),
            }
            for c in reversed(sorted_by_change[-limit:])
        ]

        result = {"gainers": gainers, "losers": losers}
        self._cache_set(cache_key, result)
        return result

    async def get_fear_greed_index(self) -> dict[str, Any]:
        cache_key = "fear_greed"
        cached = self._cache_get(cache_key, ttl=300)
        if cached is not None:
            return cached

        try:
            resp = await self._client.get(FEAR_GREED_URL, timeout=10.0)
            resp.raise_for_status()
            data = resp.json()
            entry = data["data"][0]
            result = {
                "value": int(entry["value"]),
                "classification": entry["value_classification"],
            }
            self._cache_set(cache_key, result)
            return result
        except (httpx.HTTPError, KeyError, IndexError):
            return {"value": 50, "classification": "Neutral"}
