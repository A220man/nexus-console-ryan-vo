import pytest
from httpx import AsyncClient
from datetime import datetime, timedelta


@pytest.mark.asyncio
async def test_create_opportunity(async_client: AsyncClient):
    contact_response = await async_client.post("/api/contacts", json={
        "first_name": "John",
        "last_name": "Doe",
        "email": "john.doe@example.com",
    })
    contact_id = contact_response.json()["id"]
    
    opportunity_data = {
        "name": "Enterprise Deal",
        "description": "Large enterprise contract",
        "stage": "prospecting",
        "amount": 100000,
        "probability": 25,
        "expected_close_date": (datetime.now() + timedelta(days=90)).isoformat(),
        "contact_id": contact_id,
        "company_id": None,
    }
    response = await async_client.post("/api/opportunities", json=opportunity_data)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Enterprise Deal"
    assert data["description"] == "Large enterprise contract"
    assert data["stage"] == "prospecting"
    assert data["amount"] == 100000
    assert data["probability"] == 25
    assert data["contact_id"] == contact_id
    assert "id" in data
    assert "created_at" in data
    assert "updated_at" in data
    return data["id"]


@pytest.mark.asyncio
async def test_get_opportunity(async_client: AsyncClient):
    opportunity_id = await test_create_opportunity(async_client)
    response = await async_client.get(f"/api/opportunities/{opportunity_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == opportunity_id
    assert data["name"] == "Enterprise Deal"
    assert data["stage"] == "prospecting"


@pytest.mark.asyncio
async def test_list_opportunities(async_client: AsyncClient):
    await test_create_opportunity(async_client)
    response = await async_client.get("/api/opportunities")
    assert response.status_code == 200
    data = response.json()
    assert "opportunities" in data
    assert "total" in data
    assert "page" in data
    assert "page_size" in data
    assert "total_pages" in data
    assert len(data["opportunities"]) >= 1
    assert data["opportunities"][0]["name"] == "Enterprise Deal"


@pytest.mark.asyncio
async def test_update_opportunity(async_client: AsyncClient):
    opportunity_id = await test_create_opportunity(async_client)
    update_data = {"stage": "qualification", "probability": 50, "amount": 150000}
    response = await async_client.patch(f"/api/opportunities/{opportunity_id}", json=update_data)
    assert response.status_code == 200
    data = response.json()
    assert data["stage"] == "qualification"
    assert data["probability"] == 50
    assert data["amount"] == 150000


@pytest.mark.asyncio
async def test_delete_opportunity(async_client: AsyncClient):
    opportunity_id = await test_create_opportunity(async_client)
    response = await async_client.delete(f"/api/opportunities/{opportunity_id}")
    assert response.status_code == 204
    
    response = await async_client.get(f"/api/opportunities/{opportunity_id}")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_opportunity_filter_by_stage(async_client: AsyncClient):
    contact_response = await async_client.post("/api/contacts", json={
        "first_name": "Alice",
        "last_name": "Smith",
        "email": "alice.smith@example.com",
    })
    contact_id = contact_response.json()["id"]
    
    await async_client.post("/api/opportunities", json={
        "name": "Deal 1",
        "stage": "prospecting",
        "contact_id": contact_id,
    })
    await async_client.post("/api/opportunities", json={
        "name": "Deal 2",
        "stage": "qualification",
        "contact_id": contact_id,
    })
    
    response = await async_client.get("/api/opportunities?stage=prospecting")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["opportunities"][0]["stage"] == "prospecting"
    
    response = await async_client.get("/api/opportunities?stage=qualification")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["opportunities"][0]["stage"] == "qualification"


@pytest.mark.asyncio
async def test_opportunity_filter_by_contact(async_client: AsyncClient):
    contact1_response = await async_client.post("/api/contacts", json={
        "first_name": "Contact",
        "last_name": "One",
        "email": "contact1@example.com",
    })
    contact1_id = contact1_response.json()["id"]
    
    contact2_response = await async_client.post("/api/contacts", json={
        "first_name": "Contact",
        "last_name": "Two",
        "email": "contact2@example.com",
    })
    contact2_id = contact2_response.json()["id"]
    
    await async_client.post("/api/opportunities", json={
        "name": "Deal for Contact 1",
        "contact_id": contact1_id,
    })
    await async_client.post("/api/opportunities", json={
        "name": "Deal for Contact 2",
        "contact_id": contact2_id,
    })
    
    response = await async_client.get(f"/api/opportunities?contact_id={contact1_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["opportunities"][0]["contact_id"] == contact1_id


@pytest.mark.asyncio
async def test_opportunity_filter_by_company(async_client: AsyncClient):
    contact_response = await async_client.post("/api/contacts", json={
        "first_name": "Contact",
        "last_name": "Test",
        "email": "contact.test@example.com",
    })
    contact_id = contact_response.json()["id"]
    
    company_response = await async_client.post("/api/companies", json={
        "name": "Test Company",
        "domain": "test.com",
    })
    company_id = company_response.json()["id"]
    
    await async_client.post("/api/opportunities", json={
        "name": "Deal with Company",
        "contact_id": contact_id,
        "company_id": company_id,
    })
    await async_client.post("/api/opportunities", json={
        "name": "Deal without Company",
        "contact_id": contact_id,
    })
    
    response = await async_client.get(f"/api/opportunities?company_id={company_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["opportunities"][0]["company_id"] == company_id


@pytest.mark.asyncio
async def test_opportunity_invalid_stage(async_client: AsyncClient):
    contact_response = await async_client.post("/api/contacts", json={
        "first_name": "Test",
        "last_name": "User",
        "email": "test.user@example.com",
    })
    contact_id = contact_response.json()["id"]
    
    response = await async_client.post("/api/opportunities", json={
        "name": "Bad Stage Deal",
        "stage": "invalid_stage",
        "contact_id": contact_id,
    })
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_opportunity_not_found(async_client: AsyncClient):
    response = await async_client.get("/api/opportunities/999999")
    assert response.status_code == 404
    assert response.json()["detail"] == "Opportunity not found"
    
    response = await async_client.patch("/api/opportunities/999999", json={"stage": "qualification"})
    assert response.status_code == 404
    
    response = await async_client.delete("/api/opportunities/999999")
    assert response.status_code == 404
