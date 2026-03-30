from __future__ import annotations

import pytest
from sqlalchemy import select

from crypto_intel.db import Alert, Analysis, BotStat, Database, Watchlist


@pytest.fixture
async def db():
    database = Database("sqlite+aiosqlite:///:memory:")
    await database.init()
    yield database
    await database.close()


class TestDatabaseInit:
    @pytest.mark.asyncio
    async def test_create_tables(self, db):
        session = await db.get_session()
        async with session:
            result = await session.execute(select(Alert))
            assert result.scalars().all() == []

    @pytest.mark.asyncio
    async def test_all_tables_exist(self, db):
        session = await db.get_session()
        async with session:
            for model in [Alert, Analysis, Watchlist, BotStat]:
                result = await session.execute(select(model))
                assert result.scalars().all() == []


class TestAlertCRUD:
    @pytest.mark.asyncio
    async def test_create_alert(self, db):
        session = await db.get_session()
        async with session:
            alert = Alert(
                user_id="user1",
                token="btc",
                condition="above",
                threshold=70000.0,
            )
            session.add(alert)
            await session.commit()

            result = await session.execute(select(Alert))
            alerts = result.scalars().all()
            assert len(alerts) == 1
            assert alerts[0].token == "btc"

    @pytest.mark.asyncio
    async def test_query_active_alerts(self, db):
        session = await db.get_session()
        async with session:
            session.add(Alert(user_id="u1", token="btc", condition="above", threshold=70000))
            session.add(
                Alert(user_id="u2", token="eth", condition="below", threshold=3000, active=False)
            )
            await session.commit()

            result = await session.execute(select(Alert).where(Alert.active.is_(True)))
            active = result.scalars().all()
            assert len(active) == 1
            assert active[0].token == "btc"


class TestWatchlistCRUD:
    @pytest.mark.asyncio
    async def test_add_to_watchlist(self, db):
        session = await db.get_session()
        async with session:
            session.add(Watchlist(user_id="user1", token="btc"))
            session.add(Watchlist(user_id="user1", token="eth"))
            await session.commit()

            result = await session.execute(
                select(Watchlist).where(Watchlist.user_id == "user1")
            )
            items = result.scalars().all()
            assert len(items) == 2


class TestAnalysisCRUD:
    @pytest.mark.asyncio
    async def test_store_analysis(self, db):
        session = await db.get_session()
        async with session:
            analysis = Analysis(
                token="btc",
                analysis_json='{"summary": "test"}',
                risk_level="medium",
                sentiment_score=0.3,
            )
            session.add(analysis)
            await session.commit()

            result = await session.execute(select(Analysis).where(Analysis.token == "btc"))
            saved = result.scalars().first()
            assert saved is not None
            assert saved.risk_level == "medium"
