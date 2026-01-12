from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class CreateAccountRequest(BaseModel):
    account_number: str = Field(..., examples=["123456"])
    initial_balance_cents: int = Field(0, ge=0, examples=[10000])
    currency: str = Field("BRL", min_length=3, max_length=3, examples=["BRL"])


class AccountCreatedResponse(BaseModel):
    account_id: str
    account_number: str
    balance_cents: int
    currency: str


class BalanceResponse(BaseModel):
    account_number: str
    balance_cents: int
    currency: str


class DepositRequest(BaseModel):
    amount_cents: int = Field(..., gt=0, examples=[5000])
    currency: str = Field("BRL", min_length=3, max_length=3, examples=["BRL"])


class WithdrawRequest(BaseModel):
    amount_cents: int = Field(..., gt=0, examples=[2000])
    currency: str = Field("BRL", min_length=3, max_length=3, examples=["BRL"])


class TransactionResponse(BaseModel):
    account_number: str
    balance_cents: int
    currency: str


class TransferRequest(BaseModel):
    from_account_number: str = Field(..., examples=["123456"])
    to_account_number: str = Field(..., examples=["456789"])
    amount_cents: int = Field(..., gt=0, examples=[3000])
    currency: str = Field("BRL", min_length=3, max_length=3, examples=["BRL"])


class TransferResponse(BaseModel):
    correlation_id: str
    from_account_number: str
    to_account_number: str
    from_balance_cents: int
    to_balance_cents: int
    currency: str


class TransactionEntryResponse(BaseModel):
    entry_id: UUID
    entry_type: str
    amount_cents: int
    currency: str
    correlation_id: UUID | None
    occurred_at: datetime
    counterparty_account_number: str | None
