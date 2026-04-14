from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.app.core.config import MAX_IMAGE_SIZE_BYTES
from src.db.session import get_db
from src.db.models import FaceEncodingModel, ImageModel, SessionModel
from src.schemas import ImageResponse, SessionResponse
from src.services.face_encoding import FaceEncodingServiceError, encoding_client

router = APIRouter()

@router.post("/", response_model=SessionResponse, status_code=201)
async def create_session(db: AsyncSession = Depends(get_db)):
    new_session = SessionModel()
    db.add(new_session)
    await db.commit()
    await db.refresh(new_session)
    return new_session


@router.post("/{session_id}/images", response_model=ImageResponse, status_code=201)
async def upload_image(
    session_id: UUID,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    session = await db.get(SessionModel, session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")

    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Only image uploads are supported")

    count_query = select(func.count(ImageModel.id)).where(ImageModel.session_id == session_id)
    count_result = await db.execute(count_query)
    current_count = count_result.scalar_one()
    if current_count >= 5:
        raise HTTPException(status_code=400, detail="Maximum 5 images allowed per session")

    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Uploaded file is empty")
    if len(content) > MAX_IMAGE_SIZE_BYTES:
        raise HTTPException(status_code=400, detail="Uploaded file exceeds maximum allowed size")

    filename = file.filename or "upload-image"

    try:
        vectors = await encoding_client.get_encodings(
            image_content=content,
            filename=filename,
            content_type=file.content_type,
        )
    except FaceEncodingServiceError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    if not vectors:
        raise HTTPException(status_code=400, detail="No faces detected in uploaded image")

    image = ImageModel(
        session_id=session_id,
        filename=filename,
        content_type=file.content_type,
    )
    db.add(image)
    await db.flush()

    for vector in vectors:
        db.add(FaceEncodingModel(image_id=image.id, vector=vector))

    await db.commit()

    image_query = (
        select(ImageModel)
        .options(selectinload(ImageModel.encodings))
        .where(ImageModel.id == image.id)
    )
    image_result = await db.execute(image_query)
    return image_result.scalar_one()
