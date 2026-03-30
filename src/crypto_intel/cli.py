from __future__ import annotations

import asyncio

import click
import structlog
from rich.console import Console
from rich.table import Table

from crypto_intel.config import get_settings

console = Console()
log = structlog.get_logger()


@click.group()
def cli() -> None:
    """Crypto Intel Bot — AI-powered market intelligence."""
    pass


@cli.command()
def run() -> None:
    """Start the Discord bot."""
    settings = get_settings()
    if not settings.discord_token:
        console.print("[red]DISCORD_TOKEN not set. Check your .env file.[/red]")
        raise SystemExit(1)

    from crypto_intel.bot import run_bot

    console.print("[green]Starting Crypto Intel Bot...[/green]")
    run_bot(settings)


@cli.command()
@click.argument("token")
def analyze(token: str) -> None:
    """Run analysis on a token from the command line."""

    async def _run() -> None:
        from crypto_intel.agents.orchestrator import run_analysis

        console.print(f"[cyan]Analyzing {token.upper()}...[/cyan]")
        result = await run_analysis(token)

        price_data = result.get("price_data", {})
        indicators = result.get("technical_indicators", {})

        table = Table(title=f"Analysis: {token.upper()}")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green")

        table.add_row("Price", f"${price_data.get('price', 0):,.2f}")
        table.add_row("24h Change", f"{price_data.get('change_24h', 0):+.1f}%")
        table.add_row("Market Cap", f"${price_data.get('market_cap', 0):,.0f}")
        table.add_row("RSI", f"{indicators.get('rsi', 50):.0f}")
        table.add_row("Technical Signal", indicators.get("signal", "N/A"))
        table.add_row("Sentiment", f"{result.get('sentiment_score', 0):+.2f}")
        table.add_row("Risk Level", result.get("risk_level", "N/A").upper())
        table.add_row("Confidence", f"{result.get('confidence', 0):.0%}")

        console.print(table)
        console.print(f"\n[bold]Summary:[/bold] {result.get('analysis_summary', 'N/A')}")

    asyncio.run(_run())


@cli.group()
def alerts() -> None:
    """Manage price alerts."""
    pass


@alerts.command(name="list")
def alerts_list() -> None:
    """Show all active alerts."""

    async def _run() -> None:
        from sqlalchemy import select

        from crypto_intel.db import Alert, Database

        settings = get_settings()
        db = Database(settings.database_url)
        await db.init()
        session = await db.get_session()

        async with session:
            result = await session.execute(select(Alert).where(Alert.active.is_(True)))
            active_alerts = result.scalars().all()

        if not active_alerts:
            console.print("[yellow]No active alerts.[/yellow]")
            return

        table = Table(title="Active Alerts")
        table.add_column("ID", style="dim")
        table.add_column("Token", style="cyan")
        table.add_column("Condition")
        table.add_column("Threshold", style="green")
        table.add_column("User ID", style="dim")

        for a in active_alerts:
            table.add_row(
                str(a.id), a.token.upper(), a.condition, f"${a.threshold:,.2f}", a.user_id
            )
        console.print(table)
        await db.close()

    asyncio.run(_run())


@cli.command()
def market() -> None:
    """Show market overview."""

    async def _run() -> None:
        from crypto_intel.data.coingecko import CoinGeckoClient

        client = CoinGeckoClient()
        console.print("[cyan]Fetching market data...[/cyan]")

        btc = await client.get_price("bitcoin")
        eth = await client.get_price("ethereum")
        fng = await client.get_fear_greed_index()

        table = Table(title="Market Overview")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green")

        table.add_row("BTC Price", f"${btc['price']:,.2f}")
        table.add_row("BTC 24h", f"{btc.get('change_24h', 0):+.1f}%")
        table.add_row("ETH Price", f"${eth['price']:,.2f}")
        table.add_row("ETH 24h", f"{eth.get('change_24h', 0):+.1f}%")
        table.add_row("Fear & Greed", f"{fng['value']}/100 ({fng['classification']})")

        console.print(table)
        await client.close()

    asyncio.run(_run())


@cli.command(name="init-db")
def init_db() -> None:
    """Initialize database tables."""

    async def _run() -> None:
        from crypto_intel.db import Database

        settings = get_settings()
        db = Database(settings.database_url)
        await db.init()
        console.print("[green]Database initialized.[/green]")
        await db.close()

    asyncio.run(_run())


if __name__ == "__main__":
    cli()
