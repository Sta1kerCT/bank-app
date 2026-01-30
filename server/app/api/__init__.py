"""
API Routes Package
All FastAPI routers for banking operations
"""

from .accounts import router as accounts_router
from .transactions import router as transactions_router

__all__ = ["accounts_router", "transactions_router"]

API_VERSION = "v1"