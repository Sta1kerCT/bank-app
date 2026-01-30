"""
Tests for Bank Client
Unit tests for the CLI banking client
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

SAMPLE_ACCOUNT_RESPONSE = {
    "id": 1,
    "account_number": "TEST001",
    "owner_name": "Test User",
    "balance": 1000.0,
    "is_active": True,
    "created_at": "2023-01-01T00:00:00"
}

SAMPLE_TRANSACTION_RESPONSE = {
    "id": 1,
    "from_account": None,
    "to_account": "TEST001",
    "amount": 500.0,
    "transaction_type": "DEPOSIT",
    "status": "PENDING",
    "created_at": "2023-01-01T00:00:00"
}

__all__ = ["SAMPLE_ACCOUNT_RESPONSE", "SAMPLE_TRANSACTION_RESPONSE"]