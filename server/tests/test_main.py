"""Tests for main app: root, health, metrics, lifespan."""
import pytest
from httpx import AsyncClient

from app.main import app, lifespan

@pytest.mark.asyncio
async def test_root(client: AsyncClient):
    response = await client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "Bank" in data["message"]


@pytest.mark.asyncio
async def test_health(client: AsyncClient):
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"


@pytest.mark.asyncio
async def test_metrics(client: AsyncClient):
    response = await client.get("/metrics")
    assert response.status_code == 200
    text = response.text
    assert "http_requests_total" in text or "bank_" in text or "#" in text
