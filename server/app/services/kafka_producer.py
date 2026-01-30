from kafka import KafkaProducer
import json
import os
import logging
from ..models.database import Transaction

logger = logging.getLogger(__name__)

KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
TRANSACTIONS_TOPIC = "bank-transactions"

producer = None


def get_producer():
    global producer
    if producer is None:
        try:
            producer = KafkaProducer(
                bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
                value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                acks='all',
                retries=3
            )
            logger.info(f"Connected to Kafka at {KAFKA_BOOTSTRAP_SERVERS}")
        except Exception as e:
            logger.error(f"Failed to connect to Kafka: {e}")
            raise
    return producer


async def send_transaction_event(transaction: Transaction):
    """Send transaction to Kafka for processing"""
    producer = get_producer()

    event = {
        "transaction_id": transaction.id,
        "from_account": transaction.from_account,
        "to_account": transaction.to_account,
        "amount": transaction.amount,
        "transaction_type": transaction.transaction_type,
        "created_at": transaction.created_at.isoformat() if transaction.created_at else None
    }

    try:
        future = producer.send(TRANSACTIONS_TOPIC, value=event)
        result = future.get(timeout=10)
        logger.info(f"Sent transaction {transaction.id} to Kafka: {result}")
    except Exception as e:
        logger.error(f"Failed to send transaction to Kafka: {e}")
        raise