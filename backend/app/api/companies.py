from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import Optional

from app.core.database import get_db
from app.models.company import Company
from app.schemas.company import CompanyCreate, CompanyUpdate, CompanyResponse, CompanyListResponse

router = APIRouter()


@router.get("/companies", response_model=CompanyListResponse)
async def list_companies(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: Optional[str] = Query(None),
    industry: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    query = select(Company)
    count_query = select(func.count(Company.id))

    if search:
        search_term = f"%{search}%"
        query = query.where(
            (Company.name.ilike(search_term))
            | (Company.domain.ilike(search_term))
        )
        count_query = count_query.where(
            (Company.name.ilike(search_term))
            | (Company.domain.ilike(search_term))
        )

    if industry:
        query = query.where(Company.industry == industry)
        count_query = count_query.where(Company.industry == industry)

    total = (await db.execute(count_query)).scalar_one()
    total_pages = (total + page_size - 1) // page_size

    query = query.offset((page - 1) * page_size).limit(page_size).order_by(Company.name)
    companies = (await db.execute(query)).scalars().all()

    return CompanyListResponse(
        companies=[CompanyResponse.model_validate(c) for c in companies],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.get("/companies/{company_id}", response_model=CompanyResponse)
async def get_company(company_id: int, db: AsyncSession = Depends(get_db)):
    company = await db.get(Company, company_id)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    return CompanyResponse.model_validate(company)


@router.post("/companies", response_model=CompanyResponse, status_code=status.HTTP_201_CREATED)
async def create_company(company_in: CompanyCreate, db: AsyncSession = Depends(get_db)):
    company = Company(**company_in.model_dump())
    db.add(company)
    await db.commit()
    await db.refresh(company)
    return CompanyResponse.model_validate(company)


@router.patch("/companies/{company_id}", response_model=CompanyResponse)
async def update_company(company_id: int, company_in: CompanyUpdate, db: AsyncSession = Depends(get_db)):
    company = await db.get(Company, company_id)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    for field, value in company_in.model_dump(exclude_unset=True).items():
        setattr(company, field, value)

    await db.commit()
    await db.refresh(company)
    return CompanyResponse.model_validate(company)


@router.delete("/companies/{company_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_company(company_id: int, db: AsyncSession = Depends(get_db)):
    company = await db.get(Company, company_id)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    await db.delete(company)
    await db.commit()
