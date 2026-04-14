import os
import asyncio
import pytest

DEFAULT_TEST_DATABASE_URL = "postgresql://postgres:postgres@127.0.0.1:5432/veriff"
os.environ["DATABASE_URL"] = os.getenv(
    "TEST_DATABASE_URL",
    os.getenv("DATABASE_URL", DEFAULT_TEST_DATABASE_URL),
)

from src.db.base import Base
from src.db import models
from src.db.session import engine


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(autouse=True)
async def setup_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    yield

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()
