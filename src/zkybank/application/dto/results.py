from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from zkybank.domain.entities.ledger_entry import LedgerEntryType


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


@dataclass(frozen=True, slots=True)
class LedgerEntryResult:
    entry_id: UUID
    entry_type: LedgerEntryType
    amount_cents: int
    currency: str
    correlation_id: UUID | None
    occurred_at: datetime
    counterparty_account_number: str | None
