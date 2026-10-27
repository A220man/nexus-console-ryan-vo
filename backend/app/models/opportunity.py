from sqlalchemy import String, Text, ForeignKey, Index, Integer, Numeric, DateTime, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import Optional, List
from datetime import datetime
import enum

from app.models.base import Base, TimestampMixin


class OpportunityStage(str, enum.Enum):
    PROSPECTING = "prospecting"
    QUALIFICATION = "qualification"
    PROPOSAL = "proposal"
    NEGOTIATION = "negotiation"
    CLOSED_WON = "closed_won"
    CLOSED_LOST = "closed_lost"


class Opportunity(Base, TimestampMixin):
    __tablename__ = "opportunities"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    stage: Mapped[OpportunityStage] = mapped_column(
        SQLEnum(OpportunityStage),
        default=OpportunityStage.PROSPECTING,
        nullable=False,
        index=True
    )
    amount: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    probability: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    expected_close_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    actual_close_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    contact_id: Mapped[int] = mapped_column(ForeignKey("contacts.id"), nullable=False, index=True)
    contact: Mapped["Contact"] = relationship("Contact", back_populates="opportunities")

    company_id: Mapped[Optional[int]] = mapped_column(ForeignKey("companies.id"), nullable=True, index=True)
    company: Mapped[Optional["Company"]] = relationship("Company", back_populates="opportunities")

    __table_args__ = (
        Index("ix_opportunities_stage_date", "stage", "expected_close_date"),
    )

    def __repr__(self) -> str:
        return f"<Opportunity(id={self.id}, name={self.name}, stage={self.stage.value}, amount={self.amount})>"
