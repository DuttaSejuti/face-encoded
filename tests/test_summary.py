import pytest
from httpx import ASGITransport, AsyncClient
from uuid import uuid4
from src.main import app
from src.db.models import SessionModel, ImageModel, FaceEncodingModel

@pytest.mark.asyncio
async def test_session_summary_empty(db_session):
    # 1. Create a session
    new_session = SessionModel()
    db_session.add(new_session)
    await db_session.commit()
    
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get(f"/v1/sessions/{new_session.id}/summary")
    
    assert response.status_code == 200
    data = response.json()
    assert data["total_images"] == 0
    assert data["total_faces"] == 0
    assert data["encodings"] == []

@pytest.mark.asyncio
async def test_session_summary_missing_session_returns_404():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get(f"/v1/sessions/{uuid4()}/summary")

    assert response.status_code == 404
    assert response.json() == {"detail": "Session not found"}

@pytest.mark.asyncio
async def test_session_summary_flat_list(db_session):
    # 1. Create session, image, and 2 encodings manually
    session = SessionModel()
    db_session.add(session)
    await db_session.flush()
    
    image = ImageModel(session_id=session.id, filename="test.jpg", content_type="image/jpeg")
    db_session.add(image)
    await db_session.flush()
    
    # 2 Encodings
    v1 = [1.0] * 128
    v2 = [0.5] * 128
    
    db_session.add(FaceEncodingModel(image_id=image.id, vector=v1))
    db_session.add(FaceEncodingModel(image_id=image.id, vector=v2))
    await db_session.commit()
    
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get(f"/v1/sessions/{session.id}/summary")
    
    assert response.status_code == 200
    data = response.json()
    
    # Verify flat structure
    assert data["total_images"] == 1
    assert data["total_faces"] == 2
    assert len(data["encodings"]) == 2
    assert v1 in data["encodings"]
    assert v2 in data["encodings"]
