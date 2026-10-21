import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_check(async_client: AsyncClient):
    response = await async_client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "version" in data
    assert "environment" in data


@pytest.mark.asyncio
async def test_health_check_db_not_configured(async_client: AsyncClient):
    response = await async_client.get("/api/health/db")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "not_configured"