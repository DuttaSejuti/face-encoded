import pytest
from uuid import UUID
from datetime import datetime
from src.db.models import SessionModel

@pytest.mark.asyncio
async def test_create_session(client, db_session):
    # Setup: Call API
    response = await client.post("/v1/sessions/")
    
    # Assert: Success status
    assert response.status_code == 201
    data = response.json()

    # Assert: Validate data types from response
    session_id = UUID(data["id"])
    created_at = datetime.fromisoformat(data["created_at"])
    updated_at = datetime.fromisoformat(data["updated_at"])

    # Logical check: birth must be before or equal to update
    assert created_at <= updated_at

    # Assert: Validate persistence in Database
    session = await db_session.get(SessionModel, session_id)
    assert session is not None
    assert session.id == session_id
