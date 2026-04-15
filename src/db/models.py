import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship
from src.db.base import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class SessionModel(Base):
    __tablename__ = "sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False)
    created_at = Column(
        DateTime(timezone=True),
        default=utc_now,
        nullable=False,
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=utc_now,
        onupdate=utc_now,
        nullable=False,
    )
    images = relationship("ImageModel", back_populates="session", cascade="all, delete-orphan")


class ImageModel(Base):
    __tablename__ = "images"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False)
    session_id = Column(UUID(as_uuid=True), ForeignKey("sessions.id"), nullable=False)
    filename = Column(String, nullable=False)
    content_type = Column(String, nullable=False)
    created_at = Column(
        DateTime(timezone=True),
        default=utc_now,
        nullable=False,
    )

    session = relationship("SessionModel", back_populates="images")
    encodings = relationship("FaceEncodingModel", back_populates="image", cascade="all, delete-orphan")


class FaceEncodingModel(Base):
    __tablename__ = "face_encodings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False)
    image_id = Column(UUID(as_uuid=True), ForeignKey("images.id"), nullable=False)
    vector = Column(JSONB, nullable=False)
    created_at = Column(
        DateTime(timezone=True),
        default=utc_now,
        nullable=False,
    )

    image = relationship("ImageModel", back_populates="encodings")
