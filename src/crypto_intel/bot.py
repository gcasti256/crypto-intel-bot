from __future__ import annotations

import discord
import structlog
from discord import app_commands

from crypto_intel.agents.market_data_agent import set_client as set_market_client
from crypto_intel.agents.orchestrator import run_analysis
from crypto_intel.agents.report_agent import _format_number
from crypto_intel.alerts.monitor import AlertMonitor
from crypto_intel.config import Settings
from crypto_intel.data.coingecko import CoinGeckoClient
from crypto_intel.db import Alert, Database, Watchlist

log = structlog.get_logger()


class CryptoIntelBot(discord.Client):
    def __init__(self, settings: Settings) -> None:
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(intents=intents)

        self.settings = settings
        self.tree = app_commands.CommandTree(self)
        self.coingecko = CoinGeckoClient(settings.coingecko_base_url)
        self.db = Database(settings.database_url)
        self.alert_monitor = AlertMonitor(
            db=self.db,
            coingecko=self.coingecko,
            bot=self,
            interval=settings.alert_check_interval_seconds,
        )

    async def setup_hook(self) -> None:
        await self.db.init()
        set_market_client(self.coingecko)
        _register_commands(self)
        await self.tree.sync()
        self.loop.create_task(self.alert_monitor.run())
        log.info("bot.ready")


def _risk_color(risk: str) -> int:
    return {"low": 0x22C55E, "medium": 0xEAB308, "high": 0xEF4444}.get(risk, 0x6366F1)


def _sentiment_emoji(score: float) -> str:
    if score > 0.2:
        return "Bullish"
    elif score < -0.2:
        return "Bearish"
    return "Neutral"


def _register_commands(bot: CryptoIntelBot) -> None:
    @bot.tree.command(name="analyze", description="Run full AI analysis on a token")
    @app_commands.describe(token="Token symbol (e.g. BTC, ETH, SOL)")
    async def analyze_cmd(interaction: discord.Interaction, token: str) -> None:
        await interaction.response.defer()

        try:
            result = await run_analysis(token)

            price_data = result.get("price_data", {})
            indicators = result.get("technical_indicators", {})
            risk = result.get("risk_level", "medium")
            sentiment = result.get("sentiment_score", 0.0)
            summary = result.get("analysis_summary", "No analysis available.")
            confidence = result.get("confidence", 0.5)

            embed = discord.Embed(
                title=f"Analysis: {token.upper()}",
                description=summary,
                color=_risk_color(risk),
            )
            embed.add_field(
                name="Price",
                value=(
                    f"{_format_number(price_data.get('price', 0))}\n"
                    f"24h: {price_data.get('change_24h', 0):+.1f}%"
                ),
                inline=True,
            )
            embed.add_field(
                name="Technical",
                value=(
                    f"RSI: {indicators.get('rsi', 50):.0f}\n"
                    f"Signal: {indicators.get('signal', 'N/A')}"
                ),
                inline=True,
            )
            embed.add_field(
                name="Sentiment",
                value=f"{_sentiment_emoji(sentiment)} ({sentiment:+.2f})",
                inline=True,
            )
            embed.add_field(
                name="Risk Level",
                value=f"{risk.upper()} (confidence: {confidence:.0%})",
                inline=True,
            )
            embed.set_footer(text="Crypto Intel Bot | Not financial advice")

            await interaction.followup.send(embed=embed)
        except Exception as e:
            log.error("cmd.analyze.failed", error=str(e))
            await interaction.followup.send(f"Analysis failed: {e}")

    @bot.tree.command(name="alert", description="Set a price alert")
    @app_commands.describe(
        token="Token symbol",
        condition="Alert when price goes above or below",
        price="Target price in USD",
    )
    @app_commands.choices(
        condition=[
            app_commands.Choice(name="above", value="above"),
            app_commands.Choice(name="below", value="below"),
        ]
    )
    async def alert_cmd(
        interaction: discord.Interaction,
        token: str,
        condition: app_commands.Choice[str],
        price: float,
    ) -> None:
        session = await bot.db.get_session()
        async with session:
            alert = Alert(
                user_id=str(interaction.user.id),
                guild_id=str(interaction.guild_id or ""),
                token=token.lower(),
                condition=condition.value,
                threshold=price,
            )
            session.add(alert)
            await session.commit()

        await interaction.response.send_message(
            f"Alert set: {token.upper()} {condition.value} ${price:,.2f}"
        )

    @bot.tree.command(name="sentiment", description="Get news sentiment for a token")
    @app_commands.describe(token="Token symbol")
    async def sentiment_cmd(interaction: discord.Interaction, token: str) -> None:
        await interaction.response.defer()

        try:
            from crypto_intel.agents.sentiment_agent import (
                compute_keyword_sentiment,
            )
            from crypto_intel.data.news import NewsFetcher

            fetcher = NewsFetcher()
            articles = await fetcher.fetch_all()
            filtered = NewsFetcher.filter_by_token(articles, token)
            score = compute_keyword_sentiment(filtered)

            embed = discord.Embed(
                title=f"Sentiment: {token.upper()}",
                color=0x22C55E if score > 0 else 0xEF4444 if score < 0 else 0xEAB308,
            )
            embed.add_field(
                name="Score",
                value=f"{_sentiment_emoji(score)} ({score:+.2f})",
                inline=False,
            )

            if filtered:
                headlines = "\n".join(
                    f"[{a['title']}]({a.get('link', '')})"
                    for a in filtered[:5]
                )
                embed.add_field(name="Top Headlines", value=headlines, inline=False)
            else:
                embed.add_field(name="Headlines", value="No recent news found", inline=False)

            embed.set_footer(text=f"{len(filtered)} articles analyzed")
            await interaction.followup.send(embed=embed)
        except Exception as e:
            log.error("cmd.sentiment.failed", error=str(e))
            await interaction.followup.send(f"Sentiment analysis failed: {e}")

    @bot.tree.command(name="watchlist", description="Manage your watchlist")
    @app_commands.describe(
        action="add, remove, or show",
        token="Token symbol (required for add/remove)",
    )
    @app_commands.choices(
        action=[
            app_commands.Choice(name="add", value="add"),
            app_commands.Choice(name="remove", value="remove"),
            app_commands.Choice(name="show", value="show"),
        ]
    )
    async def watchlist_cmd(
        interaction: discord.Interaction,
        action: app_commands.Choice[str],
        token: str | None = None,
    ) -> None:
        from sqlalchemy import delete, select

        user_id = str(interaction.user.id)
        session = await bot.db.get_session()

        async with session:
            if action.value == "add":
                if not token:
                    await interaction.response.send_message("Specify a token to add.")
                    return
                entry = Watchlist(user_id=user_id, token=token.lower())
                session.add(entry)
                await session.commit()
                await interaction.response.send_message(
                    f"Added {token.upper()} to your watchlist."
                )

            elif action.value == "remove":
                if not token:
                    await interaction.response.send_message("Specify a token to remove.")
                    return
                await session.execute(
                    delete(Watchlist).where(
                        Watchlist.user_id == user_id,
                        Watchlist.token == token.lower(),
                    )
                )
                await session.commit()
                await interaction.response.send_message(
                    f"Removed {token.upper()} from your watchlist."
                )

            elif action.value == "show":
                result = await session.execute(
                    select(Watchlist).where(Watchlist.user_id == user_id)
                )
                items = result.scalars().all()
                if not items:
                    await interaction.response.send_message("Your watchlist is empty.")
                    return

                tokens_list = ", ".join(w.token.upper() for w in items)
                await interaction.response.send_message(
                    f"Your watchlist: {tokens_list}"
                )

    @bot.tree.command(name="market", description="Market overview")
    async def market_cmd(interaction: discord.Interaction) -> None:
        await interaction.response.defer()

        try:
            btc_price = await bot.coingecko.get_price("bitcoin")
            gainers_losers = await bot.coingecko.get_top_gainers_losers(5)
            fng = await bot.coingecko.get_fear_greed_index()

            embed = discord.Embed(title="Market Overview", color=0x6366F1)
            embed.add_field(
                name="BTC Price",
                value=(
                    f"{_format_number(btc_price['price'])}\n"
                    f"24h: {btc_price.get('change_24h', 0):+.1f}%"
                ),
                inline=True,
            )
            embed.add_field(
                name="Fear & Greed",
                value=f"{fng['value']}/100 ({fng['classification']})",
                inline=True,
            )

            gainers_text = "\n".join(
                f"{g['symbol']}: {g['change_24h']:+.1f}%"
                for g in gainers_losers["gainers"][:5]
            )
            losers_text = "\n".join(
                f"{loser['symbol']}: {loser['change_24h']:+.1f}%"
                for loser in gainers_losers["losers"][:5]
            )

            embed.add_field(name="Top Gainers", value=gainers_text or "N/A", inline=True)
            embed.add_field(name="Top Losers", value=losers_text or "N/A", inline=True)

            await interaction.followup.send(embed=embed)
        except Exception as e:
            log.error("cmd.market.failed", error=str(e))
            await interaction.followup.send(f"Failed to fetch market data: {e}")


def run_bot(settings: Settings) -> None:
    bot = CryptoIntelBot(settings)
    bot.run(settings.discord_token)
