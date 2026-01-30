"""Tests for Kafka consumer: process_transaction and consume_transactions."""
import pytest
from unittest.mock import Mock, MagicMock, patch, AsyncMock
from sqlalchemy import select

from app.consumer import process_transaction, consume_transactions, AsyncSessionLocal
from app.models import Account, Transaction


@pytest.fixture
def sample_transaction_data():
    return {
        "transaction_id": 1,
        "from_account": "ACC001",
        "to_account": "ACC002",
        "amount": 100.0,
        "transaction_type": "TRANSFER",
        "created_at": "2023-01-01T00:00:00",
    }


@pytest.mark.asyncio
async def test_process_deposit(sample_transaction_data):
    async with AsyncSessionLocal() as session:
        session.add(Account(account_number="ACC002", owner_name="Bob", balance=50.0))
        session.add(
            Transaction(
                id=1,
                from_account=None,
                to_account="ACC002",
                amount=100.0,
                transaction_type="DEPOSIT",
                status="PENDING",
            )
        )
        await session.commit()

    deposit_data = {
        "transaction_id": 1,
        "from_account": None,
        "to_account": "ACC002",
        "amount": 100.0,
        "transaction_type": "DEPOSIT",
    }
    await process_transaction(deposit_data)

    async with AsyncSessionLocal() as session:
        r = await session.execute(select(Account).where(Account.account_number == "ACC002"))
        acc = r.scalar_one()
        assert acc.balance == 150.0
        r = await session.execute(select(Transaction).where(Transaction.id == 1))
        tx = r.scalar_one()
        assert tx.status == "COMPLETED"


@pytest.mark.asyncio
async def test_process_withdraw(sample_transaction_data):
    async with AsyncSessionLocal() as session:
        session.add(Account(account_number="ACC001", owner_name="Alice", balance=500.0))
        session.add(
            Transaction(
                id=1,
                from_account="ACC001",
                to_account="ACC001",
                amount=200.0,
                transaction_type="WITHDRAW",
                status="PENDING",
            )
        )
        await session.commit()

    withdraw_data = {
        "transaction_id": 1,
        "from_account": "ACC001",
        "to_account": "ACC001",
        "amount": 200.0,
        "transaction_type": "WITHDRAW",
    }
    await process_transaction(withdraw_data)

    async with AsyncSessionLocal() as session:
        r = await session.execute(select(Account).where(Account.account_number == "ACC001"))
        acc = r.scalar_one()
        assert acc.balance == 300.0
        r = await session.execute(select(Transaction).where(Transaction.id == 1))
        tx = r.scalar_one()
        assert tx.status == "COMPLETED"


@pytest.mark.asyncio
async def test_process_transfer(sample_transaction_data):
    async with AsyncSessionLocal() as session:
        session.add(Account(account_number="ACC001", owner_name="Alice", balance=500.0))
        session.add(Account(account_number="ACC002", owner_name="Bob", balance=100.0))
        session.add(
            Transaction(
                id=1,
                from_account="ACC001",
                to_account="ACC002",
                amount=100.0,
                transaction_type="TRANSFER",
                status="PENDING",
            )
        )
        await session.commit()

    await process_transaction(sample_transaction_data)

    async with AsyncSessionLocal() as session:
        r = await session.execute(select(Account).where(Account.account_number == "ACC001"))
        acc1 = r.scalar_one()
        assert acc1.balance == 400.0
        r = await session.execute(select(Account).where(Account.account_number == "ACC002"))
        acc2 = r.scalar_one()
        assert acc2.balance == 200.0
        r = await session.execute(select(Transaction).where(Transaction.id == 1))
        tx = r.scalar_one()
        assert tx.status == "COMPLETED"


@pytest.mark.asyncio
async def test_process_transaction_failure_sets_failed():
    """When an error occurs, transaction status is set to FAILED."""
    mock_session1 = AsyncMock()
    mock_session1.execute = AsyncMock()
    mock_session1.begin = AsyncMock()
    mock_session1.commit = AsyncMock(side_effect=Exception("db error"))
    mock_session1.rollback = AsyncMock()
    mock_session2 = AsyncMock()
    mock_session2.execute = AsyncMock()
    mock_session2.commit = AsyncMock()
    mock_cm = AsyncMock()
    mock_cm.__aenter__.side_effect = [mock_session1, mock_session2]
    mock_cm.__aexit__.return_value = None

    with patch("app.consumer.AsyncSessionLocal", return_value=mock_cm):
        await process_transaction(
            {
                "transaction_id": 99,
                "from_account": "X",
                "to_account": "Y",
                "amount": 10.0,
                "transaction_type": "TRANSFER",
            }
        )

    mock_session1.rollback.assert_called_once()
    mock_session2.commit.assert_called_once()


def test_consume_transactions_calls_process():
    """consume_transactions iterates messages and calls process_transaction."""
    mock_message = Mock()
    mock_message.value = {
        "transaction_id": 1,
        "from_account": "A",
        "to_account": "B",
        "amount": 10.0,
        "transaction_type": "DEPOSIT",
    }
    mock_consumer = MagicMock()
    mock_consumer.__iter__.return_value = iter([mock_message])

    with patch("app.consumer.KafkaConsumer", return_value=mock_consumer):
        with patch("app.consumer.process_transaction") as mock_process:
            with patch("app.consumer.asyncio.run") as mock_run:
                consume_transactions()
                assert mock_run.call_count == 1
                mock_process.assert_called_once_with(mock_message.value)


@pytest.mark.asyncio
async def test_get_db_session():
    """get_db_session yields a session and closes it."""
    from app.consumer import get_db_session

    sessions = []
    async for session in get_db_session():
        sessions.append(session)
        assert session is not None
    assert len(sessions) == 1
