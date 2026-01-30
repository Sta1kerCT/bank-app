from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


class AccountCreate(BaseModel):
    owner_name: str = Field(..., min_length=2, max_length=100)
    initial_balance: float = Field(0.0, ge=0)


class AccountResponse(BaseModel):
    id: int
    account_number: str
    owner_name: str
    balance: float
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class TransactionCreate(BaseModel):
    from_account: Optional[str] = None
    to_account: str
    amount: float = Field(..., gt=0)
    transaction_type: str = Field(..., pattern="^(DEPOSIT|WITHDRAW|TRANSFER)$")


class TransactionResponse(BaseModel):
    id: int
    from_account: Optional[str]
    to_account: str
    amount: float
    transaction_type: str
    status: str
    created_at: datetime

    class Config:
        from_attributes = True