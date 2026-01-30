"""
Test Suite for Bank Application
Pytest configuration and shared test utilities
"""

import pytest
import asyncio
from typing import Generator, AsyncGenerator

# Общие фикстуры для всех тестов
@pytest.fixture
def sample_account_data():
    """Sample account data for tests"""
    return {
        "owner_name": "Test User",
        "initial_balance": 1000.0
    }

@pytest.fixture
def sample_transaction_data():
    """Sample transaction data for tests"""
    return {
        "to_account": "TEST123",
        "amount": 500.0,
        "transaction_type": "DEPOSIT"
    }

# Фикстура для event loop (для async тестов)
@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create event loop for async tests"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

# Общие константы для тестов
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"
TEST_KAFKA_BROKER = "localhost:9092"

__all__ = [
    "sample_account_data",
    "sample_transaction_data",
    "event_loop",
    "TEST_DATABASE_URL",
    "TEST_KAFKA_BROKER"
]