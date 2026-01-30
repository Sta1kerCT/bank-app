"""Tests for Kafka producer (mocked)."""
import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

from app.services.kafka_producer import send_transaction_event, get_producer


@pytest.fixture
def mock_transaction():
    t = Mock()
    t.id = 1
    t.from_account = "ACC001"
    t.to_account = "ACC002"
    t.amount = 100.0
    t.transaction_type = "TRANSFER"
    t.created_at = datetime(2024, 1, 1, 12, 0, 0)
    return t


@pytest.mark.asyncio
async def test_send_transaction_event(mock_transaction):
    mock_future = MagicMock()
    mock_future.get.return_value = Mock(topic="bank-transactions", partition=0, offset=0)
    mock_producer = MagicMock()
    mock_producer.send.return_value = mock_future

    with patch("app.services.kafka_producer.get_producer", return_value=mock_producer):
        await send_transaction_event(mock_transaction)

    mock_producer.send.assert_called_once()
    call_args = mock_producer.send.call_args
    assert call_args[0][0] == "bank-transactions"
    event = call_args[1]["value"]
    assert event["transaction_id"] == 1
    assert event["from_account"] == "ACC001"
    assert event["to_account"] == "ACC002"
    assert event["amount"] == 100.0
    assert event["transaction_type"] == "TRANSFER"


@pytest.mark.asyncio
async def test_send_transaction_event_deposit(mock_transaction):
    mock_transaction.from_account = None
    mock_transaction.transaction_type = "DEPOSIT"
    mock_future = MagicMock()
    mock_future.get.return_value = Mock()
    mock_producer = MagicMock()
    mock_producer.send.return_value = mock_future

    with patch("app.services.kafka_producer.get_producer", return_value=mock_producer):
        await send_transaction_event(mock_transaction)

    event = mock_producer.send.call_args[1]["value"]
    assert event["from_account"] is None
    assert event["transaction_type"] == "DEPOSIT"


def test_get_producer_creates_once():
    import app.services.kafka_producer as mod
    old_producer = mod.producer
    try:
        mod.producer = None
        with patch("app.services.kafka_producer.KafkaProducer") as mock_kafka:
            mock_kafka.return_value = MagicMock()
            p1 = get_producer()
            p2 = get_producer()
            assert p1 is p2
            mock_kafka.assert_called_once()
    finally:
        mod.producer = old_producer


@pytest.mark.asyncio
async def test_send_transaction_event_raises_on_failure(mock_transaction):
    mock_producer = MagicMock()
    mock_producer.send.return_value.get.side_effect = Exception("Kafka error")
    with patch("app.services.kafka_producer.get_producer", return_value=mock_producer):
        with pytest.raises(Exception, match="Kafka error"):
            await send_transaction_event(mock_transaction)


def test_get_producer_raises_when_kafka_unavailable():
    import app.services.kafka_producer as mod
    old_producer = mod.producer
    try:
        mod.producer = None
        with patch("app.services.kafka_producer.KafkaProducer") as mock_kafka:
            mock_kafka.side_effect = Exception("Connection refused")
            with pytest.raises(Exception, match="Connection refused"):
                get_producer()
    finally:
        mod.producer = old_producer
