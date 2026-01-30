"""SQLAlchemy models for consumer (same schema as server for DB updates)."""
from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, func
from sqlalchemy.orm import declarative_base

Base = declarative_base()

__all__ = ["Base", "Account", "Transaction"]


class Account(Base):
    __tablename__ = "accounts"

    id = Column(Integer, primary_key=True, index=True)
    account_number = Column(String, unique=True, index=True, nullable=False)
    owner_name = Column(String, nullable=False)
    balance = Column(Float, default=0.0)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    from_account = Column(String, index=True)
    to_account = Column(String, index=True, nullable=False)
    amount = Column(Float, nullable=False)
    transaction_type = Column(String, nullable=False)
    status = Column(String, default="PENDING")
    created_at = Column(DateTime, server_default=func.now())
    processed_at = Column(DateTime)
