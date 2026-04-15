from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.app.core.config import MAX_IMAGE_SIZE_BYTES, MAX_IMAGE_PER_SESSION
from src.db.models import FaceEncodingModel, ImageModel, SessionModel
from src.services.face_encoding import encoding_client

"""
except SessionNotFoundError → 404
except InvalidImageError → 400
except FaceEncodingServiceError → 502
"""

class SessionImageError(Exception):
    pass


class SessionNotFoundError(SessionImageError):
    pass


class InvalidImageError(SessionImageError):
    pass


class ImageLimitExceededError(SessionImageError):
    pass


async def upload_session_image(
    db: AsyncSession,
    session_id: UUID,
    filename: str,
    content_type: str | None,
    content: bytes,
) -> ImageModel:
    session = await db.get(SessionModel, session_id)
    if session is None:
        raise SessionNotFoundError("Session not found")

    if not content_type or not content_type.startswith("image/"):
        raise InvalidImageError("Only image uploads are supported")

    count_query = select(func.count(ImageModel.id)).where(ImageModel.session_id == session_id)
    count_result = await db.execute(count_query)
    current_count = count_result.scalar_one()

    if current_count >= MAX_IMAGE_PER_SESSION:
        raise ImageLimitExceededError("Maximum 5 images allowed per session")

    if not content:
        raise InvalidImageError("Uploaded file is empty")

    if len(content) > MAX_IMAGE_SIZE_BYTES:
        raise InvalidImageError("Uploaded file exceeds maximum allowed size")

    resolved_filename = filename or "upload-image"
    vectors = await encoding_client.get_encodings(
        image_content=content,
        filename=resolved_filename,
        content_type=content_type,
    )

    if not vectors:
        raise InvalidImageError("No faces detected in uploaded image")

    try:
        image = ImageModel(
            session_id=session_id,
            filename=resolved_filename,
            content_type=content_type,
        )
        db.add(image)
        await db.flush()

        for vector in vectors:
            db.add(FaceEncodingModel(image_id=image.id, vector=vector))
        await db.commit()
    except Exception:
        await db.rollback()
        raise

    image_query = (
        select(ImageModel)
        .options(selectinload(ImageModel.encodings))
        .where(ImageModel.id == image.id)
    )
    image_result = await db.execute(image_query)
    return image_result.scalar_one()
