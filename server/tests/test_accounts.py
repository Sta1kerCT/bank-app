"""Tests for accounts API."""
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.accounts import create_account, get_account, list_accounts
from app.models.schemas import AccountCreate


@pytest.mark.asyncio
async def test_create_account(client: AsyncClient):
    response = await client.post(
        "/accounts/",
        json={"owner_name": "John Doe", "initial_balance": 1000.0},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["owner_name"] == "John Doe"
    assert data["balance"] == 1000.0
    assert "account_number" in data


@pytest.mark.asyncio
async def test_get_account(client: AsyncClient):
    create_response = await client.post(
        "/accounts/",
        json={"owner_name": "Jane Doe", "initial_balance": 500.0},
    )
    account_number = create_response.json()["account_number"]

    response = await client.get(f"/accounts/{account_number}")
    assert response.status_code == 200
    data = response.json()
    assert data["account_number"] == account_number
    assert data["owner_name"] == "Jane Doe"


@pytest.mark.asyncio
async def test_get_account_not_found(client: AsyncClient):
    response = await client.get("/accounts/NONEXISTENT")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_list_accounts(client: AsyncClient):
    for i in range(3):
        await client.post(
            "/accounts/",
            json={"owner_name": f"User {i}", "initial_balance": 100.0 * i},
        )

    response = await client.get("/accounts/")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 3


@pytest.mark.asyncio
async def test_create_account_validation(client: AsyncClient):
    response = await client.post(
        "/accounts/",
        json={"owner_name": "A", "initial_balance": -1},
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_account_unit(db_session: AsyncSession):
    result = await create_account(
        AccountCreate(owner_name="Unit Test", initial_balance=200.0),
        db_session,
    )
    assert result.owner_name == "Unit Test"
    assert result.balance == 200.0
    assert len(result.account_number) == 8


@pytest.mark.asyncio
async def test_get_account_unit(db_session: AsyncSession):
    acc = await create_account(
        AccountCreate(owner_name="Unit Get", initial_balance=50.0),
        db_session,
    )
    result = await get_account(acc.account_number, db_session)
    assert result.account_number == acc.account_number
    assert result.balance == 50.0


@pytest.mark.asyncio
async def test_get_account_not_found_unit(db_session: AsyncSession):
    from fastapi import HTTPException

    with pytest.raises(HTTPException) as exc_info:
        await get_account("NONEXISTENT", db_session)
    assert exc_info.value.status_code == 404
