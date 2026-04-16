from uuid import UUID
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from src.db.models import FaceEncodingModel, ImageModel, SessionModel
from src.services.session_images import SessionNotFoundError

async def get_session_summary(db: AsyncSession, session_id: UUID):
    session = await db.get(SessionModel, session_id)
    if session is None:
        raise SessionNotFoundError("Session not found")

    # 1. Total Images
    img_query = select(func.count(ImageModel.id)).where(ImageModel.session_id == session_id)
    img_result = await db.execute(img_query)
    total_images = img_result.scalar_one()

    # 2. Total Faces & Flat Encodings
    # Join FaceEncoding -> Image -> Session
    enc_query = (
        select(FaceEncodingModel.vector)
        .join(ImageModel)
        .where(ImageModel.session_id == session_id)
        .order_by(FaceEncodingModel.created_at)
    )
    enc_result = await db.execute(enc_query)
    vectors = enc_result.scalars().all()

    return {
        "session_id": session_id,
        "total_images": total_images,
        "total_faces": len(vectors),
        "encodings": vectors
    }
