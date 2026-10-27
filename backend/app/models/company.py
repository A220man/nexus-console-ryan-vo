from sqlalchemy import String, Text, ForeignKey, Index, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import Optional, List

from app.models.base import Base, TimestampMixin


class Company(Base, TimestampMixin):
    __tablename__ = "companies"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    domain: Mapped[Optional[str]] = mapped_column(String(255), unique=True, nullable=True, index=True)
    industry: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    size: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    annual_revenue: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    address: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    linkedin_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    website: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    contacts: Mapped[List["Contact"]] = relationship("Contact", back_populates="company")
    opportunities: Mapped[List["Opportunity"]] = relationship("Opportunity", back_populates="company")

    __table_args__ = (
        Index("ix_companies_industry", "industry"),
    )

    def __repr__(self) -> str:
        return f"<Company(id={self.id}, name={self.name}, domain={self.domain})>"
