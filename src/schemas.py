from datetime import datetime
from typing import List
from uuid import UUID
from pydantic import BaseModel, ConfigDict


class SessionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    created_at: datetime
    updated_at: datetime


class FaceEncodingResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    vector: List[float]
    created_at: datetime


class ImageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    session_id: UUID
    filename: str
    content_type: str
    created_at: datetime
    encodings: List[FaceEncodingResponse]


class SessionSummaryResponse(BaseModel):
    session_id: UUID
    total_images: int
    total_faces: int
    encodings: List[List[float]]
