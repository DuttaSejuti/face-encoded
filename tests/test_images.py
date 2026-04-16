import pytest
import respx
from httpx import Response
from sqlalchemy import select
from uuid import uuid4
from src.db.models import ImageModel, FaceEncodingModel
from src.app.core.config import MAX_IMAGE_SIZE_BYTES, FACE_ENCODING_SERVICE_URL

ENCODING_DIM = 128
SELFIE_URL = f"{FACE_ENCODING_SERVICE_URL}/v1/selfie"

@respx.mock
@pytest.mark.asyncio
async def test_upload_image_persists_encodings(client, db_session, session_id):
    # Mock encoding brain
    fake_vectors = [[0.1] * ENCODING_DIM, [0.2] * ENCODING_DIM]
    respx.post(SELFIE_URL).mock(return_value=Response(200, json=fake_vectors))

    # Action: Upload
    filename = "perfect_selfie.jpg"
    mimetype = "image/jpeg"
    files = {"file": (filename, b"fake-image-bits", mimetype)}
    response = await client.post(f"/v1/sessions/{session_id}/images", files=files)
    
    assert response.status_code == 201
    data = response.json()
    
    assert data["filename"] == filename
    assert data["content_type"] == mimetype
    assert len(data["encodings"]) == 2

    # Verify DB Persistence
    img_q = select(ImageModel).where(ImageModel.session_id == session_id)
    images = (await db_session.execute(img_q)).scalars().all()
    assert len(images) == 1
    image_id = images[0].id

    enc_q = select(FaceEncodingModel).where(FaceEncodingModel.image_id == image_id)
    encodings = (await db_session.execute(enc_q)).scalars().all()
    assert len(encodings) == 2

@pytest.mark.asyncio
async def test_upload_image_returns_404_for_missing_session(client):
    files = {"file": ("test.jpg", b"bits", "image/jpeg")}
    response = await client.post(f"/v1/sessions/{uuid4()}/images", files=files)
    assert response.status_code == 404
    assert "Session not found" in response.json()["detail"]

@respx.mock
@pytest.mark.asyncio
async def test_upload_image_enforces_max_five(client, session_id):
    respx.post(SELFIE_URL).mock(return_value=Response(200, json=[[0.1]*ENCODING_DIM]))

    for i in range(5):
        files = {"file": (f"{i}.jpg", b"bits", "image/jpeg")}
        r = await client.post(f"/v1/sessions/{session_id}/images", files=files)
        assert r.status_code == 201

    files = {"file": ("6.jpg", b"bits", "image/jpeg")}
    r = await client.post(f"/v1/sessions/{session_id}/images", files=files)
    assert r.status_code == 400
    assert "Maximum 5 images allowed" in r.json()["detail"]

@respx.mock
@pytest.mark.asyncio
async def test_upload_image_returns_502_on_encoding_service_error(client, session_id):
    respx.post(SELFIE_URL).mock(return_value=Response(500))

    files = {"file": ("test.jpg", b"bits", "image/jpeg")}
    response = await client.post(f"/v1/sessions/{session_id}/images", files=files)
    assert response.status_code == 502
    assert "Face encoding service" in response.json()["detail"]

@respx.mock
@pytest.mark.asyncio
async def test_upload_image_rejects_when_no_faces_detected(client, session_id):
    respx.post(SELFIE_URL).mock(return_value=Response(200, json=[]))

    files = {"file": ("face_less.jpg", b"bits", "image/jpeg")}
    response = await client.post(f"/v1/sessions/{session_id}/images", files=files)
    assert response.status_code == 400
    assert "No faces detected" in response.json()["detail"]

@pytest.mark.asyncio
async def test_upload_image_rejects_oversized_file(client, session_id):
    content = b"x" * (MAX_IMAGE_SIZE_BYTES + 1)
    files = {"file": ("big.jpg", content, "image/jpeg")}
    response = await client.post(f"/v1/sessions/{session_id}/images", files=files)
    assert response.status_code == 400
    assert "exceeds maximum allowed size" in response.json()["detail"]

@pytest.mark.asyncio
async def test_upload_image_rejects_invalid_type(client, session_id):
    files = {"file": ("test.txt", b"not-an-image", "text/plain")}
    response = await client.post(f"/v1/sessions/{session_id}/images", files=files)
    assert response.status_code == 400
    assert "Only image uploads are supported" in response.json()["detail"]

@pytest.mark.asyncio
async def test_upload_image_rejects_empty_file(client, session_id):
    files = {"file": ("empty.jpg", b"", "image/jpeg")}
    response = await client.post(f"/v1/sessions/{session_id}/images", files=files)
    assert response.status_code == 400
    assert "file is empty" in response.json()["detail"]
