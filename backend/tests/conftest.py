from collections.abc import AsyncIterator

import asyncpg
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.config import get_settings
from app.database import Base, get_db
from app.main import app

settings = get_settings()


def _test_database_url() -> str:
    base_url, _, db_name = settings.database_url.rpartition("/")
    return f"{base_url}/{db_name}_test"


def _maintenance_dsn() -> str:
    base_url, _, _ = settings.database_url.rpartition("/")
    return f"{base_url}/postgres".replace("postgresql+asyncpg://", "postgresql://")


async def _ensure_test_database_exists() -> None:
    db_name = _test_database_url().rsplit("/", 1)[-1]
    conn = await asyncpg.connect(_maintenance_dsn())
    try:
        await conn.execute(f'CREATE DATABASE "{db_name}"')
    except asyncpg.exceptions.DuplicateDatabaseError:
        pass
    finally:
        await conn.close()


@pytest_asyncio.fixture(scope="session")
async def test_engine() -> AsyncIterator[AsyncEngine]:
    await _ensure_test_database_exists()
    engine = create_async_engine(_test_database_url())

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(test_engine: AsyncEngine) -> AsyncIterator[AsyncSession]:
    """Wrap each test in an outer transaction that is always rolled back.

    The app's route handlers call `session.commit()` as normal — with
    `join_transaction_mode="create_savepoint"`, those commits only release a
    savepoint rather than ending the outer transaction, so nothing a test
    writes ever survives past that test.
    """
    connection = await test_engine.connect()
    outer_transaction = await connection.begin()
    session_factory = async_sessionmaker(
        bind=connection,
        expire_on_commit=False,
        join_transaction_mode="create_savepoint",
    )
    session = session_factory()

    async def override_get_db() -> AsyncIterator[AsyncSession]:
        yield session

    app.dependency_overrides[get_db] = override_get_db

    yield session

    app.dependency_overrides.pop(get_db, None)
    await session.close()
    await outer_transaction.rollback()
    await connection.close()


@pytest_asyncio.fixture
async def client(db_session: AsyncSession) -> AsyncIterator[AsyncClient]:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
