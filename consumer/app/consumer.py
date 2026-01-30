import json
from kafka import KafkaConsumer
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import select, update
import os
import logging
import asyncio
from contextlib import asynccontextmanager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://bank_user:bank_password@localhost:5432/bank_db")
KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
TRANSACTIONS_TOPIC = "bank-transactions"

engine = create_async_engine(DATABASE_URL, echo=False)
AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


@asynccontextmanager
async def get_db_session():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


async def process_transaction(transaction_data: dict):
    """Process a transaction from Kafka"""
    transaction_id = transaction_data["transaction_id"]
    from_account = transaction_data["from_account"]
    to_account = transaction_data["to_account"]
    amount = transaction_data["amount"]
    transaction_type = transaction_data["transaction_type"]

    logger.info(f"Processing transaction {transaction_id}: {transaction_type} of ${amount}")

    async with get_db_session() as session:
        try:
            # Start transaction
            await session.begin()

            # Update transaction status to processing
            await session.execute(
                update(Transaction).where(Transaction.id == transaction_id).values(status="PROCESSING")
            )

            # Process based on transaction type
            if transaction_type == "DEPOSIT":
                # Add money to account
                await session.execute(
                    update(Account)
                    .where(Account.account_number == to_account)
                    .values(balance=Account.balance + amount)
                )

            elif transaction_type == "WITHDRAW":
                # Subtract money from account
                await session.execute(
                    update(Account)
                    .where(Account.account_number == from_account)
                    .values(balance=Account.balance - amount)
                )

            elif transaction_type == "TRANSFER":
                # Transfer money between accounts
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

            # Update transaction status to completed
            from sqlalchemy import func
            await session.execute(
                update(Transaction)
                .where(Transaction.id == transaction_id)
                .values(status="COMPLETED", processed_at=func.now())
            )

            await session.commit()
            logger.info(f"Transaction {transaction_id} completed successfully")

        except Exception as e:
            await session.rollback()
            logger.error(f"Failed to process transaction {transaction_id}: {e}")

            # Update transaction status to failed
            async with get_db_session() as session2:
                await session2.execute(
                    update(Transaction)
                    .where(Transaction.id == transaction_id)
                    .values(status="FAILED")
                )
                await session2.commit()


def consume_transactions():
    """Main consumer function"""
    consumer = KafkaConsumer(
        TRANSACTIONS_TOPIC,
        bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
        value_deserializer=lambda x: json.loads(x.decode('utf-8')),
        group_id='bank-transaction-consumers',
        auto_offset_reset='earliest',
        enable_auto_commit=True
    )

    logger.info(f"Consumer started, listening on topic: {TRANSACTIONS_TOPIC}")

    for message in consumer:
        try:
            transaction_data = message.value
            logger.info(f"Received transaction: {transaction_data['transaction_id']}")

            # Process transaction asynchronously
            asyncio.run(process_transaction(transaction_data))

        except Exception as e:
            logger.error(f"Error processing message: {e}")


if __name__ == "__main__":
    # Import models here to avoid circular imports
    from server.app.models.database import Account, Transaction

    consume_transactions()