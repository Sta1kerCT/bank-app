"""
Database Models Package
SQLAlchemy models and database configuration
"""

from .database import (
    Base,
    Account,
    Transaction,
    engine,
    AsyncSessionLocal,
    get_db,
    init_db
)

__all__ = [
    "Base",
    "Account",
    "Transaction",
    "engine",
    "AsyncSessionLocal",
    "get_db",
    "init_db"
]

MODELS = {
    "Account": "Bank account with balance and owner information",
    "Transaction": "Financial transaction between accounts"
}