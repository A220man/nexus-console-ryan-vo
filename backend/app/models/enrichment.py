from sqlalchemy import String, Text, ForeignKey, Index, Enum as SQLEnum, Integer, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import Optional
from datetime import datetime
import enum

from app.models.base import Base, TimestampMixin


class EnrichmentStatus(str, enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class EnrichmentTargetType(str, enum.Enum):
    CONTACT = "contact"
    COMPANY = "company"


class EnrichmentProvider(str, enum.Enum):
    OFFLINE = "offline"
    OPENAI_COMPATIBLE = "openai_compatible"
    ANTHROPIC = "anthropic"
    GEMINI = "gemini"


class EnrichmentJob(Base, TimestampMixin):
    __tablename__ = "enrichment_jobs"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    target_type: Mapped[EnrichmentTargetType] = mapped_column(SQLEnum(EnrichmentTargetType), nullable=False, index=True)
    target_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    provider: Mapped[EnrichmentProvider] = mapped_column(SQLEnum(EnrichmentProvider), nullable=False, default=EnrichmentProvider.OFFLINE)
    status: Mapped[EnrichmentStatus] = mapped_column(SQLEnum(EnrichmentStatus), nullable=False, default=EnrichmentStatus.PENDING, index=True)
    
    # Input data snapshot for enrichment
    input_data: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Result data after enrichment
    result_data: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Error message if failed
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Timing
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    # Configuration used
    config_snapshot: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    __table_args__ = (
        Index("ix_enrichment_jobs_target", "target_type", "target_id"),
        Index("ix_enrichment_jobs_status_created", "status", "created_at"),
    )

    def __repr__(self) -> str:
        return f"<EnrichmentJob(id={self.id}, target={self.target_type}:{self.target_id}, status={self.status})>"

