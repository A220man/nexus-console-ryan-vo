from fastapi import APIRouter, Depends, HTTPException, Query, status, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

from app.core.database import get_db
from app.schemas.enrichment import (
    EnrichmentJobCreate,
    EnrichmentJobResponse,
    EnrichmentJobListResponse,
    EnrichmentResult,
    BulkEnrichmentRequest,
    EnrichmentProvider,
    EnrichmentTargetType,
    EnrichmentStatus,
)
from app.services.enrichment import enrichment_service
from app.models.enrichment import EnrichmentJob

router = APIRouter()


@router.post("/enrichment/jobs", response_model=EnrichmentJobResponse, status_code=status.HTTP_201_CREATED)
async def create_enrichment_job(
    job_in: EnrichmentJobCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """Create and start an enrichment job."""
    job = await enrichment_service.create_job(
        db=db,
        target_type=job_in.target_type,
        target_id=job_in.target_id,
        provider=job_in.provider,
        config=job_in.config,
    )
    
    # Run job in background
    background_tasks.add_task(enrichment_service.run_job, db, job.id)
    
    return EnrichmentJobResponse.model_validate(job)


@router.post("/enrichment/bulk", response_model=List[EnrichmentJobResponse], status_code=status.HTTP_201_CREATED)
async def create_bulk_enrichment_jobs(
    request: BulkEnrichmentRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """Create multiple enrichment jobs for the same target type."""
    jobs = []
    for target_id in request.target_ids:
        job = await enrichment_service.create_job(
            db=db,
            target_type=request.target_type,
            target_id=target_id,
            provider=request.provider,
            config=request.config,
        )
        jobs.append(job)
        background_tasks.add_task(enrichment_service.run_job, db, job.id)
    
    return [EnrichmentJobResponse.model_validate(j) for j in jobs]


@router.get("/enrichment/jobs", response_model=EnrichmentJobListResponse)
async def list_enrichment_jobs(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[EnrichmentStatus] = Query(None),
    target_type: Optional[EnrichmentTargetType] = Query(None),
    target_id: Optional[int] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """List enrichment jobs with optional filters."""
    jobs, total = await enrichment_service.list_jobs(
        db=db,
        page=page,
        page_size=page_size,
        status=status,
        target_type=target_type,
        target_id=target_id,
    )
    total_pages = (total + page_size - 1) // page_size
    
    return EnrichmentJobListResponse(
        jobs=[EnrichmentJobResponse.model_validate(j) for j in jobs],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.get("/enrichment/jobs/{job_id}", response_model=EnrichmentJobResponse)
async def get_enrichment_job(
    job_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Get a specific enrichment job by ID."""
    job = await db.get(EnrichmentJob, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Enrichment job not found")
    return EnrichmentJobResponse.model_validate(job)


@router.post("/enrichment/jobs/{job_id}/run", response_model=EnrichmentJobResponse)
async def run_enrichment_job(
    job_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Manually trigger an enrichment job (if pending or failed)."""
    job = await db.get(EnrichmentJob, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Enrichment job not found")
    
    if job.status not in (EnrichmentStatus.PENDING, EnrichmentStatus.FAILED):
        raise HTTPException(status_code=400, detail=f"Job cannot be run from status: {job.status}")
    
    job = await enrichment_service.run_job(db, job_id)
    return EnrichmentJobResponse.model_validate(job)


@router.post("/enrichment/jobs/{job_id}/apply", response_model=dict)
async def apply_enrichment_result(
    job_id: int,
    apply: bool = Query(True, description="Whether to apply changes to the target entity"),
    db: AsyncSession = Depends(get_db),
):
    """Apply enrichment results to the target entity."""
    result = await enrichment_service.apply_enrichment(db, job_id, apply=apply)
    if result is None:
        raise HTTPException(status_code=404, detail="Job not found, not completed, or no result data")
    return result


@router.get("/enrichment/preview", response_model=EnrichmentResult)
async def preview_enrichment(
    target_type: EnrichmentTargetType = Query(...),
    target_id: int = Query(..., ge=1),
    provider: EnrichmentProvider = Query(EnrichmentProvider.OFFLINE),
    db: AsyncSession = Depends(get_db),
):
    """Preview enrichment result without creating a job (synchronous)."""
    provider_impl = enrichment_service.get_provider(provider)
    if not provider_impl:
        if provider in (EnrichmentProvider.OPENAI_COMPATIBLE, EnrichmentProvider.ANTHROPIC, EnrichmentProvider.GEMINI):
            from app.core.config import settings
            if settings.LLM_API_KEY:
                enrichment_service.register_llm_provider(provider, settings.LLM_API_KEY, settings.LLM_BASE_URL, settings.LLM_MODEL)
                provider_impl = enrichment_service.get_provider(provider)
    
    if not provider_impl:
        raise HTTPException(status_code=400, detail=f"Provider {provider} not available")
    
    # Fetch target data
    if target_type == EnrichmentTargetType.CONTACT:
        from app.models.contact import Contact
        target = await db.get(Contact, target_id)
        if not target:
            raise HTTPException(status_code=404, detail="Contact not found")
        input_data = {
            "first_name": target.first_name,
            "last_name": target.last_name,
            "email": target.email,
            "phone": target.phone,
            "title": target.title,
            "linkedin_url": target.linkedin_url,
            "notes": target.notes,
            "company_id": target.company_id,
        }
    elif target_type == EnrichmentTargetType.COMPANY:
        from app.models.company import Company
        target = await db.get(Company, target_id)
        if not target:
            raise HTTPException(status_code=404, detail="Company not found")
        input_data = {
            "name": target.name,
            "domain": target.domain,
            "industry": target.industry,
            "size": target.size,
            "annual_revenue": target.annual_revenue,
            "description": target.description,
            "address": target.address,
            "phone": target.phone,
            "linkedin_url": target.linkedin_url,
            "website": target.website,
        }
    else:
        raise HTTPException(status_code=400, detail="Invalid target type")
    
    from app.services.enrichment import EnrichmentContext
    context = EnrichmentContext(
        target_type=target_type,
        target_id=target_id,
        input_data=input_data,
        config={},
    )
    
    result = await provider_impl.enrich(context)
    return result
