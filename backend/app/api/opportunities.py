from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import Optional
from datetime import datetime

from app.core.database import get_db
from app.models.opportunity import Opportunity, OpportunityStage
from app.schemas.opportunity import OpportunityCreate, OpportunityUpdate, OpportunityResponse, OpportunityListResponse

router = APIRouter()


@router.get("/opportunities", response_model=OpportunityListResponse)
async def list_opportunities(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    stage: Optional[OpportunityStage] = Query(None),
    contact_id: Optional[int] = Query(None),
    company_id: Optional[int] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    query = select(Opportunity)
    count_query = select(func.count(Opportunity.id))

    if stage:
        query = query.where(Opportunity.stage == stage)
        count_query = count_query.where(Opportunity.stage == stage)

    if contact_id:
        query = query.where(Opportunity.contact_id == contact_id)
        count_query = count_query.where(Opportunity.contact_id == contact_id)

    if company_id:
        query = query.where(Opportunity.company_id == company_id)
        count_query = count_query.where(Opportunity.company_id == company_id)

    total = (await db.execute(count_query)).scalar_one()
    total_pages = (total + page_size - 1) // page_size

    query = query.offset((page - 1) * page_size).limit(page_size).order_by(Opportunity.expected_close_date)
    opportunities = (await db.execute(query)).scalars().all()

    return OpportunityListResponse(
        opportunities=[OpportunityResponse.model_validate(o) for o in opportunities],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.get("/opportunities/{opportunity_id}", response_model=OpportunityResponse)
async def get_opportunity(opportunity_id: int, db: AsyncSession = Depends(get_db)):
    opportunity = await db.get(Opportunity, opportunity_id)
    if not opportunity:
        raise HTTPException(status_code=404, detail="Opportunity not found")
    return OpportunityResponse.model_validate(opportunity)


@router.post("/opportunities", response_model=OpportunityResponse, status_code=status.HTTP_201_CREATED)
async def create_opportunity(opportunity_in: OpportunityCreate, db: AsyncSession = Depends(get_db)):
    opportunity = Opportunity(**opportunity_in.model_dump())
    db.add(opportunity)
    await db.commit()
    await db.refresh(opportunity)
    return OpportunityResponse.model_validate(opportunity)


@router.patch("/opportunities/{opportunity_id}", response_model=OpportunityResponse)
async def update_opportunity(opportunity_id: int, opportunity_in: OpportunityUpdate, db: AsyncSession = Depends(get_db)):
    opportunity = await db.get(Opportunity, opportunity_id)
    if not opportunity:
        raise HTTPException(status_code=404, detail="Opportunity not found")

    for field, value in opportunity_in.model_dump(exclude_unset=True).items():
        setattr(opportunity, field, value)

    await db.commit()
    await db.refresh(opportunity)
    return OpportunityResponse.model_validate(opportunity)


@router.delete("/opportunities/{opportunity_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_opportunity(opportunity_id: int, db: AsyncSession = Depends(get_db)):
    opportunity = await db.get(Opportunity, opportunity_id)
    if not opportunity:
        raise HTTPException(status_code=404, detail="Opportunity not found")

    await db.delete(opportunity)
    await db.commit()
