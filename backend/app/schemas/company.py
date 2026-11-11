from pydantic import BaseModel, Field, ConfigDict, HttpUrl
from typing import Optional, Union
from datetime import datetime


class CompanyBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    domain: Optional[str] = Field(None, max_length=255)
    industry: Optional[str] = Field(None, max_length=100)
    size: Optional[str] = Field(None, max_length=50)
    annual_revenue: Optional[int] = Field(None, ge=0)
    description: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = Field(None, max_length=50)
    linkedin_url: Optional[Union[HttpUrl, str]] = None
    website: Optional[Union[HttpUrl, str]] = None


class CompanyCreate(CompanyBase):
    pass


class CompanyUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    domain: Optional[str] = Field(None, max_length=255)
    industry: Optional[str] = Field(None, max_length=100)
    size: Optional[str] = Field(None, max_length=50)
    annual_revenue: Optional[int] = Field(None, ge=0)
    description: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = Field(None, max_length=50)
    linkedin_url: Optional[HttpUrl] = None
    website: Optional[HttpUrl] = None


class CompanyResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    domain: Optional[str] = None
    industry: Optional[str] = None
    size: Optional[str] = None
    annual_revenue: Optional[int] = None
    description: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    linkedin_url: Optional[str] = None
    website: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class CompanyListResponse(BaseModel):
    companies: list[CompanyResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
