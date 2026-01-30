"""
Kafka Consumer Package
Processes banking transactions from Kafka
"""

from .consumer import consume_transactions, process_transaction

__version__ = "1.0.0"
__description__ = "Kafka consumer for banking transactions"

__all__ = ["consume_transactions", "process_transaction"]

CONSUMER_CONFIG = {
    "topic": "bank-transactions",
    "group_id": "bank-transaction-consumers",
    "auto_offset_reset": "earliest"
}