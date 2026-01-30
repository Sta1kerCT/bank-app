"""
Tests for Kafka Consumer
Unit tests for transaction processing
"""

TEST_TRANSACTION_DATA = {
    "transaction_id": 1,
    "from_account": "ACC001",
    "to_account": "ACC002",
    "amount": 100.0,
    "transaction_type": "TRANSFER",
    "created_at": "2023-01-01T00:00:00"
}

__all__ = ["TEST_TRANSACTION_DATA"]