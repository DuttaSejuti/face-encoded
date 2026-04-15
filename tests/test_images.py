from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient

from src.main import app
from src.services.face_encoding import FaceEncodingServiceError, encoding_client


@pytest.mark.asyncio
async def test_upload_image_persists_encodings(monkeypatch):
    monkeypatch.setattr(
        encoding_client,
        "get_encodings",
        AsyncMock(return_value=[[0.1, 0.2], [0.3, 0.4]]),
    )

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        session_response = await ac.post("/v1/sessions/")
        session_id = session_response.json()["id"]

        response = await ac.post(
            f"/v1/sessions/{session_id}/images",
            files={"file": ("face.jpg", b"image-bytes", "image/jpeg")},
        )

    assert response.status_code == 201
    data = response.json()
    assert data["session_id"] == session_id
    assert data["filename"] == "face.jpg"
    assert data["content_type"] == "image/jpeg"
    assert len(data["encodings"]) == 2


@pytest.mark.asyncio
async def test_upload_image_returns_404_for_missing_session():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.post(
            f"/v1/sessions/{uuid4()}/images",
            files={"file": ("face.jpg", b"image-bytes", "image/jpeg")},
        )

    assert response.status_code == 404
    assert response.json() == {"detail": "Session not found"}


@pytest.mark.asyncio
async def test_upload_image_enforces_max_five(monkeypatch):
    monkeypatch.setattr(
        encoding_client,
        "get_encodings",
        AsyncMock(return_value=[[0.1] * 128]),
    )

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        session_response = await ac.post("/v1/sessions/")
        session_id = session_response.json()["id"]

        for _ in range(5):
            response = await ac.post(
                f"/v1/sessions/{session_id}/images",
                files={"file": ("face.jpg", b"image-bytes", "image/jpeg")},
            )
            assert response.status_code == 201

        overflow_response = await ac.post(
            f"/v1/sessions/{session_id}/images",
            files={"file": ("face.jpg", b"image-bytes", "image/jpeg")},
        )

    assert overflow_response.status_code == 400
    assert overflow_response.json() == {"detail": "Maximum 5 images allowed per session"}


@pytest.mark.asyncio
async def test_upload_image_returns_502_on_encoding_service_error(monkeypatch):
    monkeypatch.setattr(
        encoding_client,
        "get_encodings",
        AsyncMock(side_effect=FaceEncodingServiceError("Face encoding service is unavailable.")),
    )

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        session_response = await ac.post("/v1/sessions/")
        session_id = session_response.json()["id"]

        response = await ac.post(
            f"/v1/sessions/{session_id}/images",
            files={"file": ("face.jpg", b"image-bytes", "image/jpeg")},
        )

    assert response.status_code == 502
    assert response.json() == {"detail": "Face encoding service is unavailable."}


@pytest.mark.asyncio
async def test_upload_image_rejects_oversized_file(monkeypatch):
    monkeypatch.setattr(
        encoding_client,
        "get_encodings",
        AsyncMock(return_value=[[0.1] * 128]),
    )

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        session_response = await ac.post("/v1/sessions/")
        session_id = session_response.json()["id"]

        response = await ac.post(
            f"/v1/sessions/{session_id}/images",
            files={"file": ("big.jpg", b"x" * (5 * 1024 * 1024 + 1), "image/jpeg")},
        )

    assert response.status_code == 400
    assert response.json() == {"detail": "Uploaded file exceeds maximum allowed size"}
