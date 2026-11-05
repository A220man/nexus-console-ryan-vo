from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from pydantic import BaseModel
from typing import Optional

from app.core.config import settings
from app.core.database import get_db


router = APIRouter()


class HealthResponse(BaseModel):
    status: str
    version: str
    environment: str
    database: Optional[str] = None


@router.get("/health", response_model=HealthResponse)
async def health_check():
    return HealthResponse(
        status="healthy",
        version=settings.APP_VERSION,
        environment=settings.ENVIRONMENT,
    )


class DatabaseHealthResponse(BaseModel):
    status: str
    message: Optional[str] = None


@router.get("/health/db", response_model=DatabaseHealthResponse)
async def health_check_db(db: AsyncSession = Depends(get_db)):
    try:
        await db.execute(text("SELECT 1"))
        return DatabaseHealthResponse(status="healthy", message="Database connection successful")
    except Exception as e:
        return DatabaseHealthResponse(status="unhealthy", message=f"Database connection failed: {str(e)}")