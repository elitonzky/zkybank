from __future__ import annotations

from datetime import timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session
from zkybank.adapters.outbound.persistence.sqlalchemy.models import LedgerEntryModel
from zkybank.application.ports.ledger_repository import LedgerRepository
from zkybank.domain.entities.ledger_entry import LedgerEntry, LedgerEntryType
from zkybank.domain.value_objects import AccountId, Money


class SqlAlchemyLedgerRepository(LedgerRepository):
    def __init__(self, session: Session) -> None:
        self._session = session

    def save(self, entry: LedgerEntry) -> None:
        self._session.add(
            LedgerEntryModel(
                entry_id=str(entry.entry_id),
                account_id=str(entry.account_id.value),
                entry_type=entry.entry_type.value,
                amount_cents=entry.amount.amount_cents,
                currency=entry.amount.currency,
                correlation_id=(
                    str(entry.correlation_id) if entry.correlation_id is not None else None
                ),
                occurred_at=entry.occurred_at,
            )
        )

    def list_by_account(self, account_id: AccountId) -> list[LedgerEntry]:
        stmt = select(LedgerEntryModel).where(LedgerEntryModel.account_id == str(account_id.value))
        models = self._session.execute(stmt).scalars().all()
        return [self._to_domain(m) for m in models]

    def _to_domain(self, model: LedgerEntryModel) -> LedgerEntry:
        occurred_at = model.occurred_at
        if occurred_at.tzinfo is None:
            occurred_at = occurred_at.replace(tzinfo=timezone.utc)

        correlation_id = UUID(model.correlation_id) if model.correlation_id else None

        return LedgerEntry(
            entry_id=UUID(model.entry_id),
            account_id=AccountId(value=UUID(model.account_id)),
            entry_type=LedgerEntryType(model.entry_type),
            amount=Money(amount_cents=model.amount_cents, currency=model.currency),
            correlation_id=correlation_id,
            occurred_at=occurred_at,
        )
