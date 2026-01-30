from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from ..models.database import get_db, Account
from ..models.schemas import AccountCreate, AccountResponse
import uuid
from ..monitoring.metrics import accounts_counter, accounts_balance_gauge

router = APIRouter()


@router.post("/", response_model=AccountResponse, status_code=status.HTTP_201_CREATED)
async def create_account(
        account_data: AccountCreate,
        db: AsyncSession = Depends(get_db)
):
    """Create a new bank account"""
    account_number = str(uuid.uuid4())[:8].upper()

    account = Account(
        account_number=account_number,
        owner_name=account_data.owner_name,
        balance=account_data.initial_balance
    )

    db.add(account)
    await db.commit()
    await db.refresh(account)

    accounts_counter.labels(action="create").inc()
    accounts_balance_gauge.labels(account_number=account_number).set(account.balance)

    return account


@router.get("/{account_number}", response_model=AccountResponse)
async def get_account(
        account_number: str,
        db: AsyncSession = Depends(get_db)
):
    """Get account information"""
    result = await db.execute(
        select(Account).where(Account.account_number == account_number)
    )
    account = result.scalar_one_or_none()

    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found"
        )

    return account


@router.get("/", response_model=list[AccountResponse])
async def list_accounts(
        skip: int = 0,
        limit: int = 100,
        db: AsyncSession = Depends(get_db)
):
    """List all accounts"""
    result = await db.execute(
        select(Account).offset(skip).limit(limit)
    )
    accounts = result.scalars().all()
    return accounts