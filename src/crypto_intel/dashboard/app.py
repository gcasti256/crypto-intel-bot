"""Crypto Intel Bot — Web Dashboard.

FastAPI application serving the dashboard UI and API endpoints
for market data, bot statistics, and recent analyses.
"""

from __future__ import annotations

import random
from datetime import datetime, timedelta, timezone
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

STATIC_DIR = Path(__file__).parent / "static"

dashboard = FastAPI(
    title="Crypto Intel Bot Dashboard",
    description="Real-time monitoring dashboard for the Crypto Intel Discord bot",
    version="1.0.0",
)

dashboard.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# ---------------------------------------------------------------------------
# Try importing real implementations; fall back to mock data
# ---------------------------------------------------------------------------
try:
    from crypto_intel.data.coingecko import CoinGeckoClient

    _coingecko: CoinGeckoClient | None = CoinGeckoClient()
except ImportError:
    _coingecko = None

try:
    from crypto_intel.data.database import Database

    _db: Database | None = Database()  # type: ignore[call-arg]
except ImportError:
    _db = None


# ---------------------------------------------------------------------------
# Mock data generators (used when real backends aren't available)
# ---------------------------------------------------------------------------

def _mock_market() -> dict:
    return {
        "btc_price": 87_432.18,
        "btc_24h_change": 2.34,
        "eth_price": 3_241.56,
        "eth_24h_change": -1.12,
        "fear_greed_index": 72,
        "fear_greed_label": "Greed",
        "btc_dominance": 54.3,
        "total_market_cap": 2_870_000_000_000,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }


def _mock_stats() -> dict:
    return {
        "servers": 142,
        "users": 8_740,
        "analyses_performed": 23_891,
        "alerts_triggered": 1_204,
        "uptime_hours": 2160,
    }


_MOCK_TOKENS = [
    {"symbol": "BTC", "name": "Bitcoin", "price": 87_432.18},
    {"symbol": "ETH", "name": "Ethereum", "price": 3_241.56},
    {"symbol": "SOL", "name": "Solana", "price": 172.34},
    {"symbol": "AVAX", "name": "Avalanche", "price": 38.91},
    {"symbol": "LINK", "name": "Chainlink", "price": 18.72},
    {"symbol": "DOT", "name": "Polkadot", "price": 7.83},
    {"symbol": "MATIC", "name": "Polygon", "price": 0.89},
    {"symbol": "ARB", "name": "Arbitrum", "price": 1.24},
    {"symbol": "OP", "name": "Optimism", "price": 2.67},
    {"symbol": "DOGE", "name": "Dogecoin", "price": 0.164},
    {"symbol": "PEPE", "name": "Pepe", "price": 0.0000132},
    {"symbol": "WIF", "name": "dogwifhat", "price": 2.41},
    {"symbol": "INJ", "name": "Injective", "price": 24.56},
    {"symbol": "SUI", "name": "Sui", "price": 1.87},
    {"symbol": "TIA", "name": "Celestia", "price": 12.34},
]

_RISK_LEVELS = ["Low", "Medium", "High"]
_RISK_WEIGHTS = [0.4, 0.4, 0.2]


def _mock_analyses() -> list[dict]:
    now = datetime.now(timezone.utc)
    analyses = []
    for i in range(20):
        token = random.choice(_MOCK_TOKENS)  # noqa: S311
        risk = random.choices(_RISK_LEVELS, weights=_RISK_WEIGHTS, k=1)[0]  # noqa: S311
        sentiment = round(random.uniform(0.15, 0.92), 2)  # noqa: S311
        analyses.append({
            "id": f"analysis-{1000 + i}",
            "token_symbol": token["symbol"],
            "token_name": token["name"],
            "price": token["price"],
            "risk_level": risk,
            "sentiment_score": sentiment,
            "timestamp": (now - timedelta(minutes=i * 15 + random.randint(0, 10))).isoformat(),  # noqa: S311
        })
    return analyses


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@dashboard.get("/")
async def index():
    """Serve the dashboard SPA."""
    return FileResponse(str(STATIC_DIR / "index.html"))


@dashboard.get("/api/market")
async def market_overview():
    """Return current market data (BTC, ETH, Fear & Greed, dominance)."""
    if _coingecko is not None:
        try:
            return await _coingecko.get_market_overview()
        except Exception:
            pass
    return _mock_market()


@dashboard.get("/api/analyses")
async def recent_analyses():
    """Return the 20 most recent token analyses."""
    if _db is not None:
        try:
            rows = await _db.get_recent_analyses(limit=20)
            return {"analyses": rows}
        except Exception:
            pass
    return {"analyses": _mock_analyses()}


@dashboard.get("/api/stats")
async def bot_stats():
    """Return bot usage statistics."""
    if _db is not None:
        try:
            return await _db.get_stats()
        except Exception:
            pass
    return _mock_stats()


@dashboard.get("/health")
async def health():
    """Health check endpoint for load balancers and uptime monitors."""
    return {
        "status": "healthy",
        "service": "crypto-intel-bot",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
