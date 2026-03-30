from __future__ import annotations

import datetime
from typing import Any

from sqlalchemy import Boolean, DateTime, Float, Integer, String, Text, func
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class Alert(Base):
    __tablename__ = "alerts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(String(64), index=True)
    guild_id: Mapped[str] = mapped_column(String(64), default="")
    token: Mapped[str] = mapped_column(String(32))
    condition: Mapped[str] = mapped_column(String(8))  # "above" or "below"
    threshold: Mapped[float] = mapped_column(Float)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, server_default=func.now()
    )
    triggered_at: Mapped[datetime.datetime | None] = mapped_column(DateTime, nullable=True)


class Analysis(Base):
    __tablename__ = "analyses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    token: Mapped[str] = mapped_column(String(32), index=True)
    analysis_json: Mapped[str] = mapped_column(Text)
    risk_level: Mapped[str] = mapped_column(String(16))
    sentiment_score: Mapped[float] = mapped_column(Float)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, server_default=func.now()
    )


class Watchlist(Base):
    __tablename__ = "watchlists"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(String(64), index=True)
    token: Mapped[str] = mapped_column(String(32))
    added_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, server_default=func.now()
    )


class BotStat(Base):
    __tablename__ = "bot_stats"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    metric_name: Mapped[str] = mapped_column(String(64))
    value: Mapped[float] = mapped_column(Float)
    recorded_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, server_default=func.now()
    )


class Database:
    def __init__(self, url: str) -> None:
        connect_args: dict[str, Any] = {}
        if url.startswith("sqlite"):
            connect_args["check_same_thread"] = False

        self.engine = create_async_engine(url, echo=False, connect_args=connect_args)
        self.session_factory = async_sessionmaker(self.engine, expire_on_commit=False)

    async def init(self) -> None:
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    async def get_session(self) -> AsyncSession:
        return self.session_factory()

    async def close(self) -> None:
        await self.engine.dispose()
