import pytest
import respx
from httpx import Response
from uuid import uuid4
from src.db.models import SessionModel, ImageModel, FaceEncodingModel

ENCODING_DIM = 128

@pytest.mark.asyncio
async def test_session_summary_empty(client, db_session):
    # Setup: Create a session
    new_session = SessionModel()
    db_session.add(new_session)
    await db_session.commit()
    
    response = await client.get(f"/v1/sessions/{new_session.id}/summary")
    
    assert response.status_code == 200
    data = response.json()
    assert data["total_images"] == 0
    assert data["total_faces"] == 0
    assert data["encodings"] == []

@pytest.mark.asyncio
async def test_session_summary_missing_session_returns_404(client):
    response = await client.get(f"/v1/sessions/{uuid4()}/summary")
    assert response.status_code == 404
    assert response.json() == {"detail": "Session not found"}

@pytest.mark.asyncio
async def test_session_summary_multiple_images(client, db_session):
    # Setup: 2 images, total 3 faces
    session = SessionModel()
    db_session.add(session)
    await db_session.flush()
    
    img1 = ImageModel(session_id=session.id, filename="one.jpg", content_type="image/jpeg")
    img2 = ImageModel(session_id=session.id, filename="two.jpg", content_type="image/jpeg")
    db_session.add_all([img1, img2])
    await db_session.flush()
    
    v1 = [1.0] * ENCODING_DIM
    v2 = [2.0] * ENCODING_DIM
    v3 = [3.0] * ENCODING_DIM

    # Store encodings. Note: Service uses .order_by(FaceEncodingModel.created_at)
    db_session.add(FaceEncodingModel(image_id=img1.id, vector=v1))
    await db_session.commit()
    
    db_session.add(FaceEncodingModel(image_id=img1.id, vector=v2))
    await db_session.commit()
    
    db_session.add(FaceEncodingModel(image_id=img2.id, vector=v3))
    await db_session.commit()
    
    response = await client.get(f"/v1/sessions/{session.id}/summary")
    assert response.status_code == 200
    data = response.json()
    
    assert data["total_images"] == 2
    assert data["total_faces"] == 3
    # Verify exact vectors and order (since we added them in order)
    assert data["encodings"][0] == v1
    assert data["encodings"][1] == v2
    assert data["encodings"][2] == v3

@pytest.mark.asyncio
async def test_session_summary_image_no_faces_manual(client, db_session):
    # Setup: Image exists but face detection (theoretically) found nothing
    session = SessionModel()
    db_session.add(session)
    await db_session.flush()
    
    image = ImageModel(session_id=session.id, filename="void.jpg", content_type="image/jpeg")
    db_session.add(image)
    await db_session.commit()
    
    response = await client.get(f"/v1/sessions/{session.id}/summary")
    assert response.status_code == 200
    data = response.json()
    assert data["total_images"] == 1
    assert data["total_faces"] == 0
    assert data["encodings"] == []

@respx.mock
@pytest.mark.asyncio
async def test_session_summary_full_flow(client):
    # 1. Create Session via API
    resp = await client.post("/v1/sessions/")
    session_id = resp.json()["id"]

    # 2. Mock external encoding service
    fake_vector = [0.5] * ENCODING_DIM
    # Using the path defined in FaceEncodingClient: /v1/selfie
    respx.post(url__regex=r".*/v1/selfie").mock(return_value=Response(200, json=[fake_vector]))

    # 3. Upload Image via API
    with open("ReadMe.md", "rb") as f: # Just a dummy file content
        files = {"file": ("test.jpg", f, "image/jpeg")}
        await client.post(f"/v1/sessions/{session_id}/images", files=files)

    # 4. Check Summary
    summary_resp = await client.get(f"/v1/sessions/{session_id}/summary")
    assert summary_resp.status_code == 200
    data = summary_resp.json()
    
    assert data["total_images"] == 1
    assert data["total_faces"] == 1
    assert data["encodings"][0] == fake_vector
