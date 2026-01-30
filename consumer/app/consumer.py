"""Kafka consumer: processes bank transactions from broker."""
import json
import logging
import asyncio
from kafka import KafkaConsumer
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import update, func
import os

from .models import Account, Transaction

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

_DEFAULT_URL = "postgresql+asyncpg://bank_user:bank_password@localhost:5432/bank_db"
DATABASE_URL = os.getenv("DATABASE_URL", _DEFAULT_URL)
if DATABASE_URL.startswith("postgresql://") and "+asyncpg" not in DATABASE_URL:
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)

KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
TRANSACTIONS_TOPIC = "bank-transactions"

engine = create_async_engine(DATABASE_URL, echo=False)
AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def get_db_session():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


async def process_transaction(transaction_data: dict) -> None:
    """Process a transaction from Kafka: update balances and transaction status."""
    transaction_id = transaction_data["transaction_id"]
    from_account = transaction_data.get("from_account")
    to_account = transaction_data["to_account"]
    amount = transaction_data["amount"]
    transaction_type = transaction_data["transaction_type"]

    logger.info("Processing transaction %s: %s of %s", transaction_id, transaction_type, amount)

    async with AsyncSessionLocal() as session:
        try:
            await session.begin()

            await session.execute(
                update(Transaction).where(Transaction.id == transaction_id).values(status="PROCESSING")
            )

            if transaction_type == "DEPOSIT":
                await session.execute(
                    update(Account)
                    .where(Account.account_number == to_account)
                    .values(balance=Account.balance + amount)
                )
            elif transaction_type == "WITHDRAW":
                await session.execute(
                    update(Account)
                    .where(Account.account_number == from_account)
                    .values(balance=Account.balance - amount)
                )
            elif transaction_type == "TRANSFER":
                await session.execute(
                    update(Account)
                    .where(Account.account_number == from_account)
                    .values(balance=Account.balance - amount)
                )
                await session.execute(
                    update(Account)
                    .where(Account.account_number == to_account)
                    .values(balance=Account.balance + amount)
                )

            await session.execute(
                update(Transaction)
                .where(Transaction.id == transaction_id)
                .values(status="COMPLETED", processed_at=func.now())
            )

            await session.commit()
            logger.info("Transaction %s completed successfully", transaction_id)

        except Exception as e:
            await session.rollback()
            logger.exception("Failed to process transaction %s: %s", transaction_id, e)
            async with AsyncSessionLocal() as session2:
                await session2.execute(
                    update(Transaction).where(Transaction.id == transaction_id).values(status="FAILED")
                )
                await session2.commit()


def consume_transactions() -> None:
    """Main consumer loop: read from Kafka and process each message."""
    consumer = KafkaConsumer(
        TRANSACTIONS_TOPIC,
        bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
        value_deserializer=lambda x: json.loads(x.decode("utf-8")),
        group_id="bank-transaction-consumers",
        auto_offset_reset="earliest",
        enable_auto_commit=True,
    )

    logger.info("Consumer started, listening on topic: %s", TRANSACTIONS_TOPIC)

    for message in consumer:
        try:
            transaction_data = message.value
            logger.info("Received transaction: %s", transaction_data.get("transaction_id"))
            asyncio.run(process_transaction(transaction_data))
        except Exception as e:
            logger.error("Error processing message: %s", e)


if __name__ == "__main__":
    consume_transactions()
