"""
Services Package
Business logic and external service integrations
"""

from .kafka_producer import (
    get_producer,
    send_transaction_event,
    TRANSACTIONS_TOPIC
)

__all__ = [
    "get_producer",
    "send_transaction_event",
    "TRANSACTIONS_TOPIC"
]

SERVICE_CONFIG = {
    "kafka_topic": "bank-transactions",
    "max_retries": 3
}