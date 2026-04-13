# Creating and managing database connections safely

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from src.app.core.config import get_async_db_url

engine = create_async_engine(
    get_async_db_url()
)

# expire_on_commit=False => keeps objects usable after saving
# autocommit=False => you manually control transactions
# autoflush=False => avoids unexpected DB writes
SessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

async def get_db():
    async with SessionLocal() as session:
        yield session
