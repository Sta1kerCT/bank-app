import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.database import Account
import asyncio


@pytest.mark.asyncio
async def test_create_deposit():
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Create account
        create_response = await client.post(
            "/accounts/",
            json={"owner_name": "Test User", "initial_balance": 100.0}
        )
        account_number = create_response.json()["account_number"]

        # Create deposit
        response = await client.post(
            "/transactions/",
            json={
                "to_account": account_number,
                "amount": 500.0,
                "transaction_type": "DEPOSIT"
            }
        )

        assert response.status_code == 202
        data = response.json()
        assert data["to_account"] == account_number
        assert data["amount"] == 500.0
        assert data["status"] == "PENDING"


@pytest.mark.asyncio
async def test_create_withdraw():
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Create account with balance
        create_response = await client.post(
            "/accounts/",
            json={"owner_name": "Test User", "initial_balance": 1000.0}
        )
        account_number = create_response.json()["account_number"]

        # Create withdrawal
        response = await client.post(
            "/transactions/",
            json={
                "from_account": account_number,
                "to_account": account_number,  # Same account for withdrawal
                "amount": 200.0,
                "transaction_type": "WITHDRAW"
            }
        )

        assert response.status_code == 202
        data = response.json()
        assert data["status"] == "PENDING"


@pytest.mark.asyncio
async def test_insufficient_funds():
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Create account with low balance
        create_response = await client.post(
            "/accounts/",
            json={"owner_name": "Test User", "initial_balance": 100.0}
        )
        account_number = create_response.json()["account_number"]

        # Try to withdraw more than balance
        response = await client.post(
            "/transactions/",
            json={
                "from_account": account_number,
                "to_account": account_number,
                "amount": 500.0,
                "transaction_type": "WITHDRAW"
            }
        )

        assert response.status_code == 400
        assert "Insufficient funds" in response.json()["detail"]