from __future__ import annotations

from zkybank.application.dto.results import LedgerEntryResult
from zkybank.application.errors import AccountNotFoundError
from zkybank.application.ports.unit_of_work import UnitOfWork
from zkybank.domain.value_objects import AccountNumber


class GetTransactionsUseCase:
    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    def execute(self, account_number: str) -> list[LedgerEntryResult]:
        number = AccountNumber(account_number)

        with self._uow as uow:
            account = uow.accounts.get_by_number(number)
            if account is None:
                raise AccountNotFoundError(f"Account with number {number.value} not found.")

            entries = uow.ledger.list_by_account(account.account_id)

        ordered = sorted(entries, key=lambda e: e.occurred_at, reverse=True)

        return [
            LedgerEntryResult(
                entry_id=e.entry_id,
                entry_type=e.entry_type,
                amount_cents=e.amount.amount_cents,
                currency=e.amount.currency,
                correlation_id=e.correlation_id,
                occurred_at=e.occurred_at,
                counterparty_account_number=(
                    e.counterparty_account_number.value
                    if e.counterparty_account_number is not None
                    else None
                ),
            )
            for e in ordered
        ]
