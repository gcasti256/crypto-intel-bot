from __future__ import annotations

import asyncio
import datetime
from typing import TYPE_CHECKING, Any

import structlog
from sqlalchemy import select, update

from crypto_intel.data.coingecko import CoinGeckoClient
from crypto_intel.db import Alert, Database

if TYPE_CHECKING:
    import discord

log = structlog.get_logger()


class AlertMonitor:
    def __init__(
        self,
        db: Database,
        coingecko: CoinGeckoClient,
        bot: discord.Client | None = None,
        interval: int = 60,
    ) -> None:
        self.db = db
        self.coingecko = coingecko
        self.bot = bot
        self.interval = interval
        self._running = False

    async def check_alerts(self) -> list[dict[str, Any]]:
        triggered: list[dict[str, Any]] = []
        session = await self.db.get_session()

        try:
            async with session:
                result = await session.execute(
                    select(Alert).where(Alert.active.is_(True))
                )
                alerts = result.scalars().all()

                token_prices: dict[str, float] = {}
                tokens = {a.token for a in alerts}
                for token in tokens:
                    try:
                        token_id = self.coingecko.resolve_token(token)
                        data = await self.coingecko.get_price(token_id)
                        token_prices[token] = data["price"]
                    except Exception:
                        log.warning("alert.price_fetch_failed", token=token)

                for alert in alerts:
                    price = token_prices.get(alert.token)
                    if price is None:
                        continue

                    should_trigger = False
                    if alert.condition == "above" and price >= alert.threshold:
                        should_trigger = True
                    elif alert.condition == "below" and price <= alert.threshold:
                        should_trigger = True

                    if should_trigger:
                        now = datetime.datetime.now()
                        await session.execute(
                            update(Alert)
                            .where(Alert.id == alert.id)
                            .values(active=False, triggered_at=now)
                        )
                        triggered.append({
                            "alert_id": alert.id,
                            "user_id": alert.user_id,
                            "token": alert.token,
                            "condition": alert.condition,
                            "threshold": alert.threshold,
                            "current_price": price,
                        })

                await session.commit()
        except Exception:
            log.exception("alert.check_failed")

        return triggered

    async def notify_user(self, alert_data: dict[str, Any]) -> None:
        if self.bot is None:
            return

        try:
            user = await self.bot.fetch_user(int(alert_data["user_id"]))
            token = alert_data["token"].upper()
            condition = alert_data["condition"]
            threshold = alert_data["threshold"]
            price = alert_data["current_price"]

            msg = (
                f"**Price Alert Triggered!**\n"
                f"{token} is now **${price:,.2f}** "
                f"({condition} ${threshold:,.2f})"
            )
            await user.send(msg)
        except Exception:
            log.warning("alert.notify_failed", user_id=alert_data["user_id"])

    async def run(self) -> None:
        self._running = True
        log.info("alert.monitor.started", interval=self.interval)

        while self._running:
            triggered = await self.check_alerts()
            for alert_data in triggered:
                log.info("alert.triggered", **alert_data)
                await self.notify_user(alert_data)

            await asyncio.sleep(self.interval)

    def stop(self) -> None:
        self._running = False
