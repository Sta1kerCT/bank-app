"""
Bank Client Package
Command-line interface for banking operations
"""

from .app import BankClient, cli

__version__ = "1.0.0"
__author__ = "Bank Client Team"

__all__ = ["BankClient", "cli"]

DEFAULT_SERVER_URL = "http://localhost:8000"
COMMANDS = ["create", "info", "list", "deposit", "withdraw", "transfer", "demo"]