import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_company(async_client: AsyncClient):
    company_data = {
        "name": "Acme Corporation",
        "domain": "acme.com",
        "industry": "Technology",
        "size": "100-500",
        "annual_revenue": 5000000,
        "description": "A leading tech company",
        "address": "123 Main St, San Francisco, CA",
        "phone": "+1-555-123-4567",
        "linkedin_url": "https://linkedin.com/company/acme",
        "website": "https://acme.com",
    }
    response = await async_client.post("/api/companies", json=company_data)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Acme Corporation"
    assert data["domain"] == "acme.com"
    assert data["industry"] == "Technology"
    assert data["size"] == "100-500"
    assert data["annual_revenue"] == 5000000
    assert "id" in data
    assert "created_at" in data
    assert "updated_at" in data
    return data["id"]


@pytest.mark.asyncio
async def test_get_company(async_client: AsyncClient):
    company_id = await test_create_company(async_client)
    response = await async_client.get(f"/api/companies/{company_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == company_id
    assert data["name"] == "Acme Corporation"
    assert data["domain"] == "acme.com"


@pytest.mark.asyncio
async def test_list_companies(async_client: AsyncClient):
    await test_create_company(async_client)
    response = await async_client.get("/api/companies")
    assert response.status_code == 200
    data = response.json()
    assert "companies" in data
    assert "total" in data
    assert "page" in data
    assert "page_size" in data
    assert "total_pages" in data
    assert len(data["companies"]) >= 1
    assert data["companies"][0]["name"] == "Acme Corporation"


@pytest.mark.asyncio
async def test_update_company(async_client: AsyncClient):
    company_id = await test_create_company(async_client)
    update_data = {"name": "Acme Corp", "industry": "Software"}
    response = await async_client.patch(f"/api/companies/{company_id}", json=update_data)
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Acme Corp"
    assert data["industry"] == "Software"
    assert data["domain"] == "acme.com"


@pytest.mark.asyncio
async def test_delete_company(async_client: AsyncClient):
    company_id = await test_create_company(async_client)
    response = await async_client.delete(f"/api/companies/{company_id}")
    assert response.status_code == 204
    
    response = await async_client.get(f"/api/companies/{company_id}")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_company_search(async_client: AsyncClient):
    await async_client.post("/api/companies", json={
        "name": "TechStart Inc",
        "domain": "techstart.com",
    })
    await async_client.post("/api/companies", json={
        "name": "DataFlow LLC",
        "domain": "dataflow.io",
    })
    
    response = await async_client.get("/api/companies?search=techstart")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["companies"][0]["name"] == "TechStart Inc"
    
    response = await async_client.get("/api/companies?search=inc")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1


@pytest.mark.asyncio
async def test_company_filter_by_industry(async_client: AsyncClient):
    await async_client.post("/api/companies", json={
        "name": "TechCorp",
        "industry": "Technology",
    })
    await async_client.post("/api/companies", json={
        "name": "FinanceCorp",
        "industry": "Finance",
    })
    
    response = await async_client.get("/api/companies?industry=Technology")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["companies"][0]["industry"] == "Technology"


@pytest.mark.asyncio
async def test_company_duplicate_domain(async_client: AsyncClient):
    company_data = {
        "name": "Company One",
        "domain": "unique-domain.com",
    }
    response1 = await async_client.post("/api/companies", json=company_data)
    assert response1.status_code == 201
    
    response2 = await async_client.post("/api/companies", json={
        "name": "Company Two",
        "domain": "unique-domain.com",
    })
    assert response2.status_code == 422


@pytest.mark.asyncio
async def test_company_not_found(async_client: AsyncClient):
    response = await async_client.get("/api/companies/999999")
    assert response.status_code == 404
    assert response.json()["detail"] == "Company not found"
    
    response = await async_client.patch("/api/companies/999999", json={"name": "Test"})
    assert response.status_code == 404
    
    response = await async_client.delete("/api/companies/999999")
    assert response.status_code == 404

