from pydantic import BaseModel, Field, ConfigDict, HttpUrl, field_validator
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum


class EnrichmentTargetType(str, Enum):
    CONTACT = "contact"
    COMPANY = "company"


class EnrichmentProvider(str, Enum):
    OFFLINE = "offline"
    OPENAI_COMPATIBLE = "openai_compatible"
    ANTHROPIC = "anthropic"
    GEMINI = "gemini"


class EnrichmentStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class EnrichmentJobCreate(BaseModel):
    target_type: EnrichmentTargetType
    target_id: int = Field(..., ge=1)
    provider: EnrichmentProvider = EnrichmentProvider.OFFLINE
    config: Optional[Dict[str, Any]] = None


class EnrichmentJobResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    target_type: EnrichmentTargetType
    target_id: int
    provider: EnrichmentProvider
    status: EnrichmentStatus
    input_data: Optional[Dict[str, Any]] = None
    result_data: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    config_snapshot: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime

    @field_validator("input_data", "result_data", "config_snapshot", mode="before")
    @classmethod
    def parse_json_fields(cls, v):
        if isinstance(v, str):
            import json
            try:
                return json.loads(v)
            except (json.JSONDecodeError, TypeError):
                return None
        return v


class EnrichmentJobListResponse(BaseModel):
    jobs: List[EnrichmentJobResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class EnrichmentResult(BaseModel):
    """Standardized enrichment result structure."""
    model_config = ConfigDict(extra="allow")
    
    # Contact fields
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    title: Optional[str] = None
    linkedin_url: Optional[HttpUrl] = None
    notes: Optional[str] = None
    
    # Company fields
    name: Optional[str] = None
    domain: Optional[str] = None
    industry: Optional[str] = None
    size: Optional[str] = None
    annual_revenue: Optional[int] = None
    description: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    linkedin_url: Optional[HttpUrl] = None
    website: Optional[HttpUrl] = None
    
    # Metadata
    confidence_score: Optional[float] = Field(None, ge=0.0, le=1.0)
    sources: List[str] = []
    enriched_at: datetime = Field(default_factory=datetime.utcnow)
    provider: EnrichmentProvider = EnrichmentProvider.OFFLINE


class BulkEnrichmentRequest(BaseModel):
    target_type: EnrichmentTargetType
    target_ids: List[int] = Field(..., min_length=1, max_length=100)
    provider: EnrichmentProvider = EnrichmentProvider.OFFLINE
    config: Optional[Dict[str, Any]] = None

