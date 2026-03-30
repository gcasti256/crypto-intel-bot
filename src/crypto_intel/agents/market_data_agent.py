from __future__ import annotations

import structlog

from crypto_intel.agents.state import AnalysisState
from crypto_intel.data.coingecko import CoinGeckoClient

log = structlog.get_logger()

_client: CoinGeckoClient | None = None


def set_client(client: CoinGeckoClient) -> None:
    global _client
    _client = client


def get_client() -> CoinGeckoClient:
    global _client
    if _client is None:
        _client = CoinGeckoClient()
    return _client


async def market_data_agent(state: AnalysisState) -> AnalysisState:
    token = state["token"]
    client = get_client()

    token_id = client.resolve_token(token)
    if not token_id or token_id == token.lower():
        searched = await client.search_token(token)
        if searched:
            token_id = searched

    log.info("agent.market_data", token=token, token_id=token_id)

    price_data = await client.get_price(token_id)
    price_history = await client.get_market_chart(token_id, days=14)

    return {
        "token_id": token_id,
        "price_data": price_data,
        "price_history": price_history,
    }
