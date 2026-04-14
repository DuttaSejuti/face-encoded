from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from src.db.session import get_db
from src.db.models import SessionModel
from src.schemas import SessionResponse

router = APIRouter()

@router.post("/", response_model=SessionResponse, status_code=201)
async def create_session(db: AsyncSession = Depends(get_db)):
    new_session = SessionModel()
    db.add(new_session)
    await db.commit()
    await db.refresh(new_session)
    return new_session
