from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from ..models.database import get_db, Account, Transaction
from ..models.schemas import TransactionCreate, TransactionResponse
from ..services.kafka_producer import send_transaction_event
from ..monitoring.metrics import transactions_counter, transaction_amount_gauge
import asyncio

router = APIRouter()


@router.post("/", response_model=TransactionResponse, status_code=status.HTTP_202_ACCEPTED)
async def create_transaction(
        transaction_data: TransactionCreate,
        db: AsyncSession = Depends(get_db)
):
    """Create a new transaction (will be processed by consumer)"""

    result = await db.execute(
        select(Account).where(Account.account_number == transaction_data.to_account)
    )
    to_account = result.scalar_one_or_none()

    if not to_account or not to_account.is_active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recipient account not found or inactive"
        )

    if transaction_data.transaction_type in ["WITHDRAW", "TRANSFER"]:
        if not transaction_data.from_account:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="from_account is required for this transaction type"
            )

        result = await db.execute(
            select(Account).where(Account.account_number == transaction_data.from_account)
        )
        from_account = result.scalar_one_or_none()

        if not from_account or not from_account.is_active:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Sender account not found or inactive"
            )

        if from_account.balance < transaction_data.amount:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Insufficient funds"
            )

    transaction = Transaction(
        from_account=transaction_data.from_account,
        to_account=transaction_data.to_account,
        amount=transaction_data.amount,
        transaction_type=transaction_data.transaction_type,
        status="PENDING"
    )

    db.add(transaction)
    await db.commit()
    await db.refresh(transaction)

    await send_transaction_event(transaction)

    transactions_counter.labels(
        type=transaction_data.transaction_type,
        status="pending"
    ).inc()

    transaction_amount_gauge.labels(
        transaction_id=str(transaction.id)
    ).set(transaction_data.amount)

    return transaction


@router.get("/{transaction_id}", response_model=TransactionResponse)
async def get_transaction(
        transaction_id: int,
        db: AsyncSession = Depends(get_db)
):
    """Get transaction status"""
    result = await db.execute(
        select(Transaction).where(Transaction.id == transaction_id)
    )
    transaction = result.scalar_one_or_none()

    if not transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transaction not found"
        )

    return transaction