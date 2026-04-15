import os
import asyncio
import pytest
import pytest_asyncio
from alembic import command
from alembic.config import Config

DEFAULT_TEST_DATABASE_URL = "postgresql://postgres:postgres@127.0.0.1:5432/veriff_test"
os.environ["DATABASE_URL"] = os.getenv(
    "TEST_DATABASE_URL",
    DEFAULT_TEST_DATABASE_URL,
)

from src.db.session import engine
from src.db.models import FaceEncodingModel, ImageModel, SessionModel
from sqlalchemy import delete


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session", autouse=True)
def apply_migrations():
    alembic_cfg = Config("alembic.ini")
    alembic_cfg.set_main_option("sqlalchemy.url", os.environ["DATABASE_URL"])
    command.upgrade(alembic_cfg, "head")
    yield


@pytest_asyncio.fixture(autouse=True)
async def clean_sessions():
    async with engine.begin() as conn:
        await conn.execute(delete(FaceEncodingModel))
        await conn.execute(delete(ImageModel))
        await conn.execute(delete(SessionModel))

    yield
