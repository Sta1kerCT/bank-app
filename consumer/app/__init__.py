"""Kafka consumer package: processes banking transactions from broker."""

from .consumer import consume_transactions, process_transaction

__version__ = "1.0.0"
__all__ = ["consume_transactions", "process_transaction"]