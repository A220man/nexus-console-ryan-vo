from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from pydantic import BaseModel
from typing import Optional

from app.core.config import settings


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


@router.get("/health/db")
async def health_check_db():
    # This will be implemented when database is configured
    return {"status": "not_configured", "message": "Database not yet configured"}