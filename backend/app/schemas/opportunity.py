from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime
from enum import Enum


class OpportunityStage(str, Enum):
    PROSPECTING = "prospecting"
    QUALIFICATION = "qualification"
    PROPOSAL = "proposal"
    NEGOTIATION = "negotiation"
    CLOSED_WON = "closed_won"
    CLOSED_LOST = "closed_lost"


class OpportunityBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    stage: OpportunityStage = Field(default=OpportunityStage.PROSPECTING)
    amount: Optional[int] = Field(None, ge=0)
    probability: int = Field(default=0, ge=0, le=100)
    expected_close_date: Optional[datetime] = None
    contact_id: int
    company_id: Optional[int] = None


class OpportunityCreate(OpportunityBase):
    pass


class OpportunityUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    stage: Optional[OpportunityStage] = None
    amount: Optional[int] = Field(None, ge=0)
    probability: Optional[int] = Field(None, ge=0, le=100)
    expected_close_date: Optional[datetime] = None
    actual_close_date: Optional[datetime] = None
    contact_id: Optional[int] = None
    company_id: Optional[int] = None


class OpportunityResponse(OpportunityBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime
    actual_close_date: Optional[datetime] = None


class OpportunityListResponse(BaseModel):
    opportunities: list[OpportunityResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
