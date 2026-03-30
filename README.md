# Crypto Intel Bot

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![CI](https://github.com/gcasti256/crypto-intel-bot/actions/workflows/ci.yml/badge.svg)](https://github.com/gcasti256/crypto-intel-bot/actions)

AI-powered Discord bot that delivers real-time crypto market intelligence through a multi-agent LangGraph pipeline. Combines technical analysis, news sentiment via RAG, and LLM-generated insights to produce actionable market reports.

## Architecture

```mermaid
graph TD
    A[Discord Command / CLI] --> B[Orchestrator]
    B --> C[Market Data Agent]
    C --> D[CoinGecko API]
    C --> E[Technical Agent]
    C --> F[Sentiment Agent]
    E --> G[Indicators Engine]
    F --> H[News RSS Feeds]
    F --> I[RAG Retriever]
    I --> J[Vector Store]
    E --> K[Report Agent]
    F --> K
    K --> L[LLM Provider]
    L --> M[Groq / Template Fallback]
    K --> N[Discord Embed / CLI Output]

    style B fill:#6366f1,color:#fff
    style C fill:#3b82f6,color:#fff
    style E fill:#3b82f6,color:#fff
    style F fill:#3b82f6,color:#fff
    style K fill:#3b82f6,color:#fff
```

### Agent Pipeline

```
Token Input
    │
    ▼
┌─────────────────┐
│  Market Data     │  ← CoinGecko API (price, volume, market cap)
│  Agent           │
└────────┬────────┘
         │
    ┌────┴────┐
    │         │
    ▼         ▼
┌────────┐ ┌──────────┐
│Technical│ │Sentiment │  ← Parallel execution
│Agent    │ │Agent     │
└────┬───┘ └────┬─────┘
     │          │
     └────┬─────┘
          ▼
┌─────────────────┐
│  Report Agent    │  ← Synthesizes all signals
└─────────────────┘
```

## Features

- **Multi-agent analysis pipeline** — LangGraph orchestrates market data, technical, sentiment, and report agents
- **Technical indicators** — RSI, MACD, Bollinger Bands, SMA/EMA computed from raw price data (numpy)
- **News sentiment** — RSS aggregation from CoinDesk, CoinTelegraph, Decrypt with keyword-based scoring
- **RAG retrieval** — Hash-based TF-IDF embeddings with cosine similarity for relevant news context
- **Price alerts** — Background monitoring with Discord DM notifications when thresholds are hit
- **Watchlists** — Per-user token tracking with persistent storage
- **Graceful LLM fallback** — Groq (Llama 3.1 8B) for AI summaries, template-based reports when no API key
- **Discord slash commands** — `/analyze`, `/alert`, `/sentiment`, `/watchlist`, `/market`
- **CLI interface** — Run analysis, view market data, and manage alerts from the terminal

## Quick Start

```bash
# Clone
git clone https://github.com/gcasti256/crypto-intel-bot.git
cd crypto-intel-bot

# Install
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

# Configure
cp .env.example .env
# Edit .env with your Discord bot token

# Initialize database
crypto-intel init-db

# Run the bot
crypto-intel run
```

### CLI Usage (no Discord needed)

```bash
# Analyze a token
crypto-intel analyze btc

# Market overview
crypto-intel market

# Manage alerts
crypto-intel alerts list
```

## Discord Commands

| Command | Description |
|---------|-------------|
| `/analyze <token>` | Full AI analysis with price, technicals, sentiment, risk level |
| `/alert <token> <above\|below> <price>` | Set a price alert — bot DMs you when triggered |
| `/sentiment <token>` | News sentiment score with top headlines |
| `/watchlist <add\|remove\|show> [token]` | Manage your personal watchlist |
| `/market` | Market overview — BTC price, gainers/losers, Fear & Greed Index |

## Configuration

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `DISCORD_TOKEN` | Yes | — | Discord bot token |
| `DISCORD_CLIENT_ID` | Yes | — | Discord application client ID |
| `GROQ_API_KEY` | No | — | Groq API key for LLM summaries (falls back to templates) |
| `DATABASE_URL` | No | `sqlite:///data/crypto_intel.db` | Database connection string |
| `LOG_LEVEL` | No | `INFO` | Logging level |
| `ALERT_CHECK_INTERVAL_SECONDS` | No | `60` | How often to check price alerts |
| `NEWS_REFRESH_INTERVAL_SECONDS` | No | `300` | How often to refresh news feeds |

## Tech Stack

- **Agent Framework**: LangGraph + LangChain Core
- **LLM**: Groq (Llama 3.1 8B) with template fallback
- **Discord**: discord.py with slash commands
- **Data**: CoinGecko API (free tier), RSS feeds (feedparser)
- **Analysis**: numpy, scikit-learn for technical indicators and embeddings
- **Database**: SQLAlchemy 2.0 async (PostgreSQL/SQLite)
- **CLI**: Click + Rich for terminal UI
- **Testing**: pytest + pytest-asyncio

## Project Structure

```
crypto-intel-bot/
├── src/crypto_intel/
│   ├── agents/              # LangGraph multi-agent pipeline
│   │   ├── state.py         # Shared TypedDict state
│   │   ├── market_data_agent.py
│   │   ├── technical_agent.py
│   │   ├── sentiment_agent.py
│   │   ├── report_agent.py
│   │   └── orchestrator.py  # StateGraph definition
│   ├── alerts/              # Price alert system
│   │   ├── models.py        # Alert Pydantic models
│   │   └── monitor.py       # Background alert checker
│   ├── data/                # External data sources
│   │   ├── coingecko.py     # CoinGecko API client
│   │   ├── news.py          # RSS feed aggregator
│   │   └── indicators.py    # Technical analysis (RSI, MACD, BB)
│   ├── llm/                 # LLM provider abstraction
│   │   ├── provider.py      # Protocol definition
│   │   ├── groq_provider.py # Groq implementation
│   │   ├── template_provider.py
│   │   └── factory.py       # Provider factory
│   ├── rag/                 # Retrieval-augmented generation
│   │   ├── embeddings.py    # Hash-based TF-IDF embedder
│   │   ├── store.py         # In-memory vector store
│   │   └── retriever.py     # High-level retrieval interface
│   ├── bot.py               # Discord bot with slash commands
│   ├── cli.py               # Click CLI
│   ├── config.py            # pydantic-settings configuration
│   └── db.py                # SQLAlchemy models + async engine
├── tests/                   # 60+ tests
├── .github/workflows/ci.yml
├── pyproject.toml
└── .env.example
```

## Testing

```bash
# Run all tests
PYTHONPATH=src pytest tests/ -v

# With coverage
PYTHONPATH=src pytest tests/ -v --cov=crypto_intel

# Lint
ruff check src/ tests/
```

## Deployment

```bash
# Production with PostgreSQL
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/crypto_intel
DISCORD_TOKEN=your_token
GROQ_API_KEY=your_key  # optional

crypto-intel init-db
crypto-intel run
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/new-indicator`)
3. Write tests for new functionality
4. Ensure `ruff check` and `pytest` pass
5. Submit a pull request

## License

MIT License - see [LICENSE](LICENSE) for details.
