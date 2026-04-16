from uuid import UUID
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
from src.db.session import get_db
from src.db.models import SessionModel
from src.schemas import ImageResponse, SessionResponse
from src.services.face_encoding import FaceEncodingServiceError
from src.services.session_images import (
    ImageLimitExceededError,
    InvalidImageError,
    SessionNotFoundError,
    upload_session_image,
)
from src.schemas import SessionSummaryResponse
from src.services.session_summary import get_session_summary

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
    content = await file.read()

    try:
        return await upload_session_image(
            db=db,
            session_id=session_id,
            filename=file.filename or "upload-image",
            content_type=file.content_type,
            content=content,
        )
    except SessionNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except (InvalidImageError, ImageLimitExceededError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except FaceEncodingServiceError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.get("/{session_id}/summary", response_model=SessionSummaryResponse)
async def get_summary(session_id: UUID, db: AsyncSession = Depends(get_db)):
    summary = await get_session_summary(db, session_id)
    if not summary:
        raise HTTPException(status_code=404, detail="Session not found")
    return summary
