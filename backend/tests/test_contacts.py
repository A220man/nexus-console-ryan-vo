import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_contact(async_client: AsyncClient):
    contact_data = {
        "first_name": "John",
        "last_name": "Doe",
        "email": "john.doe@example.com",
        "phone": "+1-555-123-4567",
        "title": "Software Engineer",
        "company_id": None,
    }
    response = await async_client.post("/api/contacts", json=contact_data)
    assert response.status_code == 201
    data = response.json()
    assert data["first_name"] == "John"
    assert data["last_name"] == "Doe"
    assert data["email"] == "john.doe@example.com"
    assert data["phone"] == "+1-555-123-4567"
    assert data["title"] == "Software Engineer"
    assert "id" in data
    assert "created_at" in data
    assert "updated_at" in data
    return data["id"]


@pytest.mark.asyncio
async def test_get_contact(async_client: AsyncClient):
    contact_id = await test_create_contact(async_client)
    response = await async_client.get(f"/api/contacts/{contact_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == contact_id
    assert data["first_name"] == "John"
    assert data["last_name"] == "Doe"
    assert data["email"] == "john.doe@example.com"


@pytest.mark.asyncio
async def test_list_contacts(async_client: AsyncClient):
    await test_create_contact(async_client)
    response = await async_client.get("/api/contacts")
    assert response.status_code == 200
    data = response.json()
    assert "contacts" in data
    assert "total" in data
    assert "page" in data
    assert "page_size" in data
    assert "total_pages" in data
    assert len(data["contacts"]) >= 1
    assert data["contacts"][0]["first_name"] == "John"


@pytest.mark.asyncio
async def test_update_contact(async_client: AsyncClient):
    contact_id = await test_create_contact(async_client)
    update_data = {"first_name": "Jane", "title": "Senior Software Engineer"}
    response = await async_client.patch(f"/api/contacts/{contact_id}", json=update_data)
    assert response.status_code == 200
    data = response.json()
    assert data["first_name"] == "Jane"
    assert data["title"] == "Senior Software Engineer"
    assert data["last_name"] == "Doe"
    assert data["email"] == "john.doe@example.com"


@pytest.mark.asyncio
async def test_delete_contact(async_client: AsyncClient):
    contact_id = await test_create_contact(async_client)
    response = await async_client.delete(f"/api/contacts/{contact_id}")
    assert response.status_code == 204
    
    response = await async_client.get(f"/api/contacts/{contact_id}")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_contact_search(async_client: AsyncClient):
    await async_client.post("/api/contacts", json={
        "first_name": "Alice",
        "last_name": "Smith",
        "email": "alice.smith@example.com",
    })
    await async_client.post("/api/contacts", json={
        "first_name": "Bob",
        "last_name": "Jones",
        "email": "bob.jones@example.com",
    })
    
    response = await async_client.get("/api/contacts?search=alice")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["contacts"][0]["first_name"] == "Alice"
    
    response = await async_client.get("/api/contacts?search=smith")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["contacts"][0]["last_name"] == "Smith"


@pytest.mark.asyncio
async def test_contact_duplicate_email(async_client: AsyncClient):
    contact_data = {
        "first_name": "John",
        "last_name": "Doe",
        "email": "duplicate@example.com",
    }
    response1 = await async_client.post("/api/contacts", json=contact_data)
    assert response1.status_code == 201
    
    response2 = await async_client.post("/api/contacts", json=contact_data)
    assert response2.status_code == 422


@pytest.mark.asyncio
async def test_contact_not_found(async_client: AsyncClient):
    response = await async_client.get("/api/contacts/999999")
    assert response.status_code == 404
    assert response.json()["detail"] == "Contact not found"
    
    response = await async_client.patch("/api/contacts/999999", json={"first_name": "Test"})
    assert response.status_code == 404
    
    response = await async_client.delete("/api/contacts/999999")
    assert response.status_code == 404


