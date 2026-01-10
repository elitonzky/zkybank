from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True, slots=True)
class AccountCreatedResult:
    account_id: UUID
    account_number: str
    balance_cents: int
    currency: str


@dataclass(frozen=True, slots=True)
class BalanceResult:
    account_number: str
    balance_cents: int
    currency: str


@dataclass(frozen=True, slots=True)
class TransactionResult:
    account_number: str
    balance_cents: int
    currency: str


@dataclass(frozen=True, slots=True)
class TransferResult:
    correlation_id: UUID
    from_account_number: str
    to_account_number: str
    from_balance_cents: int
    to_balance_cents: int
    currency: str
