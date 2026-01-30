"""Tests for transactions API."""
import pytest
from unittest.mock import AsyncMock, patch
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.transactions import create_transaction, get_transaction
from app.models.schemas import TransactionCreate
from app.models.database import Account


@pytest.mark.asyncio
async def test_create_deposit(client: AsyncClient):
    create_response = await client.post(
        "/accounts/",
        json={"owner_name": "Test User", "initial_balance": 100.0},
    )
    account_number = create_response.json()["account_number"]

    response = await client.post(
        "/transactions/",
        json={
            "to_account": account_number,
            "amount": 500.0,
            "transaction_type": "DEPOSIT",
        },
    )

    assert response.status_code == 202
    data = response.json()
    assert data["to_account"] == account_number
    assert data["amount"] == 500.0
    assert data["status"] == "PENDING"


@pytest.mark.asyncio
async def test_create_withdraw(client: AsyncClient):
    create_response = await client.post(
        "/accounts/",
        json={"owner_name": "Test User", "initial_balance": 1000.0},
    )
    account_number = create_response.json()["account_number"]

    response = await client.post(
        "/transactions/",
        json={
            "from_account": account_number,
            "to_account": account_number,
            "amount": 200.0,
            "transaction_type": "WITHDRAW",
        },
    )

    assert response.status_code == 202
    data = response.json()
    assert data["status"] == "PENDING"


@pytest.mark.asyncio
async def test_insufficient_funds(client: AsyncClient):
    create_response = await client.post(
        "/accounts/",
        json={"owner_name": "Test User", "initial_balance": 100.0},
    )
    account_number = create_response.json()["account_number"]

    response = await client.post(
        "/transactions/",
        json={
            "from_account": account_number,
            "to_account": account_number,
            "amount": 500.0,
            "transaction_type": "WITHDRAW",
        },
    )

    assert response.status_code == 400
    assert "Insufficient funds" in response.json()["detail"]


@pytest.mark.asyncio
async def test_transaction_to_nonexistent_account(client: AsyncClient):
    response = await client.post(
        "/transactions/",
        json={
            "to_account": "NONEXISTENT",
            "amount": 100.0,
            "transaction_type": "DEPOSIT",
        },
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_withdraw_without_from_account(client: AsyncClient):
    create_response = await client.post(
        "/accounts/",
        json={"owner_name": "Test User", "initial_balance": 100.0},
    )
    account_number = create_response.json()["account_number"]

    response = await client.post(
        "/transactions/",
        json={
            "to_account": account_number,
            "amount": 50.0,
            "transaction_type": "WITHDRAW",
        },
    )
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_get_transaction(client: AsyncClient):
    create_response = await client.post(
        "/accounts/",
        json={"owner_name": "Test User", "initial_balance": 100.0},
    )
    account_number = create_response.json()["account_number"]
    tx_response = await client.post(
        "/transactions/",
        json={
            "to_account": account_number,
            "amount": 50.0,
            "transaction_type": "DEPOSIT",
        },
    )
    tx_id = tx_response.json()["id"]

    response = await client.get(f"/transactions/{tx_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == tx_id
    assert data["amount"] == 50.0

@pytest.mark.asyncio
async def test_get_transaction_not_found(client: AsyncClient):
    response = await client.get("/transactions/99999")
    assert response.status_code == 404

@pytest.mark.asyncio
async def test_create_transaction_unit(db_session: AsyncSession):
    acc = Account(account_number="UNIT01", owner_name="U", balance=100.0)
    db_session.add(acc)
    await db_session.commit()
    await db_session.refresh(acc)
    with patch("app.api.transactions.send_transaction_event", new_callable=AsyncMock):
        result = await create_transaction(
            TransactionCreate(
                to_account="UNIT01", amount=25.0, transaction_type="DEPOSIT"
            ),
            db_session,
        )
    assert result.to_account == "UNIT01"
    assert result.amount == 25.0
    assert result.status == "PENDING"


@pytest.mark.asyncio
async def test_create_transaction_transfer_unit(db_session: AsyncSession):
    a1 = Account(account_number="T1", owner_name="A", balance=100.0)
    a2 = Account(account_number="T2", owner_name="B", balance=0.0)
    db_session.add_all([a1, a2])
    await db_session.commit()
    with patch("app.api.transactions.send_transaction_event", new_callable=AsyncMock):
        result = await create_transaction(
            TransactionCreate(
                from_account="T1",
                to_account="T2",
                amount=30.0,
                transaction_type="TRANSFER",
            ),
            db_session,
        )
    assert result.transaction_type == "TRANSFER"
    assert result.status == "PENDING"


@pytest.mark.asyncio
async def test_get_transaction_unit(db_session: AsyncSession):
    from app.models.database import Transaction

    acc = Account(account_number="G1", owner_name="X", balance=0.0)
    db_session.add(acc)
    await db_session.commit()
    tx = Transaction(
        from_account=None,
        to_account="G1",
        amount=10.0,
        transaction_type="DEPOSIT",
        status="PENDING",
    )
    db_session.add(tx)
    await db_session.commit()
    await db_session.refresh(tx)
    result = await get_transaction(tx.id, db_session)
    assert result.id == tx.id
    assert result.amount == 10.0


@pytest.mark.asyncio
async def test_get_transaction_not_found_unit(db_session: AsyncSession):
    from fastapi import HTTPException

    with pytest.raises(HTTPException) as exc_info:
        await get_transaction(99999, db_session)
    assert exc_info.value.status_code == 404


@pytest.mark.asyncio
async def test_create_transaction_sender_not_found_unit(db_session: AsyncSession):
    from fastapi import HTTPException

    acc = Account(account_number="TO1", owner_name="B", balance=0.0)
    db_session.add(acc)
    await db_session.commit()
    with patch("app.api.transactions.send_transaction_event", new_callable=AsyncMock):
        with pytest.raises(HTTPException) as exc_info:
            await create_transaction(
                TransactionCreate(
                    from_account="NO_SUCH",
                    to_account="TO1",
                    amount=10.0,
                    transaction_type="TRANSFER",
                ),
                db_session,
            )
    assert exc_info.value.status_code == 404


@pytest.mark.asyncio
async def test_create_transaction_inactive_recipient_unit(db_session: AsyncSession):
    from fastapi import HTTPException

    acc = Account(account_number="INACT", owner_name="X", balance=0.0, is_active=False)
    db_session.add(acc)
    await db_session.commit()
    with patch("app.api.transactions.send_transaction_event", new_callable=AsyncMock):
        with pytest.raises(HTTPException) as exc_info:
            await create_transaction(
                TransactionCreate(
                    to_account="INACT", amount=10.0, transaction_type="DEPOSIT"
                ),
                db_session,
            )
    assert exc_info.value.status_code == 404
