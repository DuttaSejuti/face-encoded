import os
from dotenv import load_dotenv

load_dotenv()

PROJECT_NAME = "Face Encoding Service"
API_V1_STR = "/v1"

POSTGRES_USER = os.getenv("POSTGRES_USER", "postgres")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "postgres")
POSTGRES_SERVER = os.getenv("POSTGRES_SERVER", "localhost")
POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")
POSTGRES_DB = os.getenv("POSTGRES_DB", "veriff")
DATABASE_URL = os.getenv("DATABASE_URL")

def get_sync_db_url() -> str:
    if DATABASE_URL:
        return DATABASE_URL

    return (
        f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}"
        f"@{POSTGRES_SERVER}:{POSTGRES_PORT}/{POSTGRES_DB}"
    )

def get_async_db_url() -> str:
    sync_url = get_sync_db_url()
    return sync_url.replace("postgresql://", "postgresql+asyncpg://", 1)
