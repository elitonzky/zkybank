from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy import desc, select
from sqlalchemy.orm import Session
from zkybank.adapters.outbound.persistence.sqlalchemy.models import LedgerEntryModel
from zkybank.application.ports.ledger_repository import LedgerRepository
from zkybank.domain.entities.ledger_entry import LedgerEntry, LedgerEntryType
from zkybank.domain.value_objects import AccountId, AccountNumber, Money


def _uuid_to_str(value: Any) -> str:
    if isinstance(value, UUID):
        return str(value)
    return str(value)


class SqlAlchemyLedgerRepository(LedgerRepository):
    def __init__(self, session: Session) -> None:
        self._session = session

    def save(self, entry: LedgerEntry) -> None:
        model = self._to_model(entry)
        self._session.add(model)
        self._session.flush()

    def list_by_account(self, account_id: AccountId) -> list[LedgerEntry]:
        stmt = (
            select(LedgerEntryModel)
            .where(LedgerEntryModel.account_id == _uuid_to_str(account_id.value))
            .order_by(desc(LedgerEntryModel.occurred_at))
        )
        models = self._session.execute(stmt).scalars().all()
        return [self._to_domain(m) for m in models]

    def _to_model(self, entry: LedgerEntry) -> LedgerEntryModel:
        return LedgerEntryModel(
            entry_id=_uuid_to_str(entry.entry_id),
            account_id=_uuid_to_str(entry.account_id.value),
            entry_type=entry.entry_type.value,
            amount_cents=entry.amount.amount_cents,
            currency=entry.amount.currency,
            correlation_id=_uuid_to_str(entry.correlation_id) if entry.correlation_id else None,
            counterparty_account_number=(
                entry.counterparty_account_number.value
                if entry.counterparty_account_number is not None
                else None
            ),
            occurred_at=entry.occurred_at,
        )

    def _to_domain(self, model: LedgerEntryModel) -> LedgerEntry:
        return LedgerEntry(
            entry_id=UUID(model.entry_id),
            account_id=AccountId(UUID(model.account_id)),
            entry_type=LedgerEntryType(model.entry_type),
            amount=Money(amount_cents=model.amount_cents, currency=model.currency),
            correlation_id=UUID(model.correlation_id) if model.correlation_id else None,
            counterparty_account_number=(
                AccountNumber(model.counterparty_account_number)
                if model.counterparty_account_number
                else None
            ),
            occurred_at=model.occurred_at,
        )
