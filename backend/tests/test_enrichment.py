import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_enrichment_job_contact(async_client: AsyncClient):
    """Test creating an enrichment job for a contact."""
    # First create a contact
    contact_data = {
        "first_name": "John",
        "last_name": "Doe",
        "email": "john.doe@example.com",
        "phone": "+1-555-0123",
    }
    response = await async_client.post("/api/contacts", json=contact_data)
    assert response.status_code == 201
    contact_id = response.json()["id"]

    # Create enrichment job
    job_data = {
        "target_type": "contact",
        "target_id": contact_id,
        "provider": "offline",
    }
    response = await async_client.post("/api/enrichment/jobs", json=job_data)
    assert response.status_code == 201
    data = response.json()
    assert data["target_type"] == "contact"
    assert data["target_id"] == contact_id
    assert data["provider"] == "offline"
    assert data["status"] == "pending"


@pytest.mark.asyncio
async def test_create_enrichment_job_company(async_client: AsyncClient):
    """Test creating an enrichment job for a company."""
    company_data = {
        "name": "Acme Corp",
        "domain": "acme.com",
        "industry": "Technology",
    }
    response = await async_client.post("/api/companies", json=company_data)
    assert response.status_code == 201
    company_id = response.json()["id"]

    job_data = {
        "target_type": "company",
        "target_id": company_id,
        "provider": "offline",
    }
    response = await async_client.post("/api/enrichment/jobs", json=job_data)
    assert response.status_code == 201
    data = response.json()
    assert data["target_type"] == "company"
    assert data["target_id"] == company_id
    assert data["provider"] == "offline"
    assert data["status"] == "pending"


@pytest.mark.asyncio
async def test_bulk_enrichment_jobs(async_client: AsyncClient):
    """Test creating bulk enrichment jobs."""
    # Create multiple contacts
    contact_ids = []
    for i in range(3):
        contact_data = {
            "first_name": f"User{i}",
            "last_name": f"Test{i}",
            "email": f"user{i}@example.com",
        }
        response = await async_client.post("/api/contacts", json=contact_data)
        assert response.status_code == 201
        contact_ids.append(response.json()["id"])

    # Create bulk enrichment
    bulk_data = {
        "target_type": "contact",
        "target_ids": contact_ids,
        "provider": "offline",
    }
    response = await async_client.post("/api/enrichment/bulk", json=bulk_data)
    assert response.status_code == 201
    data = response.json()
    assert len(data) == 3
    for job in data:
        assert job["target_type"] == "contact"
        assert job["target_id"] in contact_ids
        assert job["provider"] == "offline"
        assert job["status"] == "pending"


@pytest.mark.asyncio
async def test_list_enrichment_jobs(async_client: AsyncClient):
    """Test listing enrichment jobs with filters."""
    # Create a contact and enrichment job
    contact_data = {
        "first_name": "Filter",
        "last_name": "Test",
        "email": "filter.test@example.com",
    }
    response = await async_client.post("/api/contacts", json=contact_data)
    assert response.status_code == 201
    contact_id = response.json()["id"]

    job_data = {
        "target_type": "contact",
        "target_id": contact_id,
        "provider": "offline",
    }
    await async_client.post("/api/enrichment/jobs", json=job_data)

    # List all jobs
    response = await async_client.get("/api/enrichment/jobs")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 1
    assert len(data["jobs"]) >= 1

    # Filter by target_type
    response = await async_client.get("/api/enrichment/jobs", params={"target_type": "contact"})
    assert response.status_code == 200
    data = response.json()
    for job in data["jobs"]:
        assert job["target_type"] == "contact"

    # Filter by target_id
    response = await async_client.get("/api/enrichment/jobs", params={"target_id": contact_id})
    assert response.status_code == 200
    data = response.json()
    for job in data["jobs"]:
        assert job["target_id"] == contact_id


@pytest.mark.asyncio
async def test_get_enrichment_job(async_client: AsyncClient):
    """Test getting a specific enrichment job."""
    contact_data = {
        "first_name": "Get",
        "last_name": "Job",
        "email": "get.job@example.com",
    }
    response = await async_client.post("/api/contacts", json=contact_data)
    assert response.status_code == 201
    contact_id = response.json()["id"]

    job_data = {
        "target_type": "contact",
        "target_id": contact_id,
        "provider": "offline",
    }
    response = await async_client.post("/api/enrichment/jobs", json=job_data)
    assert response.status_code == 201
    job_id = response.json()["id"]

    # Get the job
    response = await async_client.get(f"/api/enrichment/jobs/{job_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == job_id
    assert data["target_type"] == "contact"
    assert data["target_id"] == contact_id


@pytest.mark.asyncio
async def test_get_enrichment_job_not_found(async_client: AsyncClient):
    """Test getting a non-existent enrichment job."""
    response = await async_client.get("/api/enrichment/jobs/999999")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_preview_enrichment_contact(async_client: AsyncClient):
    """Test preview enrichment for a contact."""
    contact_data = {
        "first_name": "Preview",
        "last_name": "Contact",
        "email": "preview.contact@acme.com",
    }
    response = await async_client.post("/api/contacts", json=contact_data)
    assert response.status_code == 201
    contact_id = response.json()["id"]

    response = await async_client.get(
        "/api/enrichment/preview",
        params={"target_type": "contact", "target_id": contact_id, "provider": "offline"}
    )
    assert response.status_code == 200
    data = response.json()
    # Enriched fields should be populated
    assert data.get("title") is not None
    assert data.get("linkedin_url") is not None


@pytest.mark.asyncio
async def test_preview_enrichment_company(async_client: AsyncClient):
    """Test preview enrichment for a company."""
    # Create company with placeholder name to test domain inference
    company_data = {
        "name": "Unknown",
        "domain": "stripe.com",
    }
    response = await async_client.post("/api/companies", json=company_data)
    assert response.status_code == 201
    company_id = response.json()["id"]

    response = await async_client.get(
        "/api/enrichment/preview",
        params={"target_type": "company", "target_id": company_id, "provider": "offline"}
    )
    assert response.status_code == 200
    data = response.json()
    # Should infer Stripe from stripe.com
    assert data.get("name") == "Stripe"
    assert data.get("domain") == "stripe.com"


@pytest.mark.asyncio
async def test_preview_enrichment_company_ai_domain(async_client: AsyncClient):
    """Test preview enrichment for a company with .ai domain."""
    company_data = {
        "name": "Example AI",
        "domain": "example.ai",
    }
    response = await async_client.post("/api/companies", json=company_data)
    assert response.status_code == 201
    company_id = response.json()["id"]

    response = await async_client.get(
        "/api/enrichment/preview",
        params={"target_type": "company", "target_id": company_id, "provider": "offline"}
    )
    assert response.status_code == 200
    data = response.json()
    # .ai TLD should map to Artificial Intelligence
    assert data.get("industry") == "Artificial Intelligence"


@pytest.mark.asyncio
async def test_preview_enrichment_not_found(async_client: AsyncClient):
    """Test preview enrichment for non-existent entity."""
    response = await async_client.get(
        "/api/enrichment/preview",
        params={"target_type": "contact", "target_id": 999999, "provider": "offline"}
    )
    assert response.status_code == 404
