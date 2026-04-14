import pytest
from httpx import ASGITransport, AsyncClient
from src.main import app


@pytest.mark.asyncio
async def test_create_session():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.post("/v1/sessions/")

    assert response.status_code == 201
    data = response.json()
    assert "id" in data
    assert "created_at" in data
    assert "updated_at" in data
