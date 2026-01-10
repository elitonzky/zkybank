from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from uuid import UUID, uuid4

from zkybank.domain.value_objects import AccountId, Money


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
    occurred_at: datetime

    @staticmethod
    def create(
        account_id: AccountId,
        entry_type: LedgerEntryType,
        amount: Money,
        correlation_id: UUID | None = None,
        occurred_at: datetime | None = None,
    ) -> LedgerEntry:
        """Factory method to create a new LedgerEntry."""
        return LedgerEntry(
            entry_id=uuid4(),
            account_id=account_id,
            entry_type=entry_type,
            amount=amount,
            correlation_id=correlation_id,
            occurred_at=occurred_at or datetime.now(timezone.utc),
        )
