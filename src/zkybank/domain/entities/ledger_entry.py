from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from uuid import UUID, uuid4

from zkybank.domain.value_objects import AccountId, AccountNumber, Money


class LedgerEntryType(Enum):
    DEPOSIT = "DEPOSIT"
    WITHDRAWAL = "WITHDRAWAL"
    TRANSFER_IN = "TRANSFER_IN"
    TRANSFER_OUT = "TRANSFER_OUT"


@dataclass(frozen=True, slots=True)
class LedgerEntry:
    entry_id: UUID
    account_id: AccountId
    entry_type: LedgerEntryType
    amount: Money
    correlation_id: UUID | None
    counterparty_account_number: AccountNumber | None
    occurred_at: datetime

    @staticmethod
    def create(
        account_id: AccountId,
        entry_type: LedgerEntryType,
        amount: Money,
        correlation_id: UUID | None = None,
        counterparty_account_number: AccountNumber | None = None,
        occurred_at: datetime | None = None,
    ) -> "LedgerEntry":
        return LedgerEntry(
            entry_id=uuid4(),
            account_id=account_id,
            entry_type=entry_type,
            amount=amount,
            correlation_id=correlation_id,
            counterparty_account_number=counterparty_account_number,
            occurred_at=occurred_at or datetime.now(timezone.utc),
        )
