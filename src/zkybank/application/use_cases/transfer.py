from __future__ import annotations

import logging
from uuid import UUID, uuid4

from zkybank.application.dto.commands import TransferCommand
from zkybank.application.dto.results import TransferResult
from zkybank.application.errors import (
    AccountNotFoundError,
    ConcurrencyConflictError,
    SameAccountTransferError,
)
from zkybank.application.ports.unit_of_work import UnitOfWork
from zkybank.domain.entities.account import Account
from zkybank.domain.entities.ledger_entry import LedgerEntry, LedgerEntryType
from zkybank.domain.value_objects import AccountNumber, Money

logger = logging.getLogger(__name__)


class TransferUseCase:
    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    def execute(self, command: TransferCommand) -> TransferResult:
        source_number = AccountNumber(command.from_account_number)
        destination_number = AccountNumber(command.to_account_number)

        self._ensure_distinct_accounts(source_number, destination_number)

        amount = Money(amount_cents=command.amount_cents, currency=command.currency)
        correlation_id = uuid4()

        for attempt in range(3):
            try:
                source_account, destination_account = self._execute_single_attempt(
                    source_number=source_number,
                    destination_number=destination_number,
                    amount=amount,
                    correlation_id=correlation_id,
                )

                self._log_transfer_succeeded(
                    correlation_id=correlation_id,
                    source_account=source_account,
                    destination_account=destination_account,
                    amount=amount,
                    attempt=attempt + 1,
                )

                return TransferResult(
                    correlation_id=correlation_id,
                    from_account_number=source_account.account_number.value,
                    to_account_number=destination_account.account_number.value,
                    from_balance_cents=source_account.balance.amount_cents,
                    to_balance_cents=destination_account.balance.amount_cents,
                    currency=amount.currency,
                )

            except ConcurrencyConflictError:
                self._log_transfer_conflict_retry(
                    correlation_id=correlation_id,
                    source_number=source_number,
                    destination_number=destination_number,
                    attempt=attempt + 1,
                )
                continue

        raise ConcurrencyConflictError("Transfer failed after retries")

    def _execute_single_attempt(
        self,
        source_number: AccountNumber,
        destination_number: AccountNumber,
        amount: Money,
        correlation_id: UUID,
    ) -> tuple[Account, Account]:
        """Execute one transfer attempt within a transactional boundary."""
        with self._uow as uow:
            locked_a, locked_b = self._load_accounts_with_stable_locks(
                uow=uow,
                source_number=source_number,
                destination_number=destination_number,
            )
            source_account, destination_account = self._map_transfer_direction(
                locked_a=locked_a,
                locked_b=locked_b,
                source_number=source_number,
            )

            source_account.withdraw(amount)
            destination_account.deposit(amount)

            self._persist_ledger_entries(
                uow=uow,
                source_account=source_account,
                destination_account=destination_account,
                amount=amount,
                correlation_id=correlation_id,
            )

            uow.accounts.save(source_account)
            uow.accounts.save(destination_account)
            uow.commit()

        return source_account, destination_account

    def _ensure_distinct_accounts(
        self,
        source_number: AccountNumber,
        destination_number: AccountNumber,
    ) -> None:
        if source_number.value == destination_number.value:
            raise SameAccountTransferError("Cannot transfer to the same account.")

    def _load_accounts_with_stable_locks(
        self,
        uow: UnitOfWork,
        source_number: AccountNumber,
        destination_number: AccountNumber,
    ) -> tuple[Account, Account]:
        """Load both accounts using a stable lock order.

        Accounts are fetched in ascending account_number order, not in (source, destination)
        order. This reduces deadlock risk when concurrent transfers involve the same pair
        of accounts in opposite directions (e.g., 123->456 and 456->123).

        Returns:
            (lower_account, higher_account) by account_number ordering, used only for lock acquisition.
        """
        lower_number, higher_number = sorted(
            [source_number, destination_number],
            key=lambda n: n.value,
        )

        lower_account = uow.accounts.get_by_number_for_update(lower_number)
        higher_account = uow.accounts.get_by_number_for_update(higher_number)

        if lower_account is None or higher_account is None:
            raise AccountNotFoundError("One or both accounts not found.")

        return lower_account, higher_account

    def _map_transfer_direction(
        self,
        locked_a: Account,
        locked_b: Account,
        source_number: AccountNumber,
    ) -> tuple[Account, Account]:
        """Map locked accounts to (source_account, destination_account)."""
        if locked_a.account_number.value == source_number.value:
            return locked_a, locked_b
        return locked_b, locked_a

    def _persist_ledger_entries(
        self,
        uow: UnitOfWork,
        source_account: Account,
        destination_account: Account,
        amount: Money,
        correlation_id: UUID,
    ) -> None:
        uow.ledger.save(
            LedgerEntry.create(
                account_id=source_account.account_id,
                entry_type=LedgerEntryType.TRANSFER_OUT,
                amount=amount,
                correlation_id=correlation_id,
                counterparty_account_number=destination_account.account_number,
            )
        )
        uow.ledger.save(
            LedgerEntry.create(
                account_id=destination_account.account_id,
                entry_type=LedgerEntryType.TRANSFER_IN,
                amount=amount,
                correlation_id=correlation_id,
                counterparty_account_number=source_account.account_number,
            )
        )

    def _log_transfer_conflict_retry(
        self,
        correlation_id: UUID,
        source_number: AccountNumber,
        destination_number: AccountNumber,
        attempt: int,
    ) -> None:
        logger.warning(
            "transfer_concurrency_conflict_retry",
            extra={
                "correlation_id": str(correlation_id),
                "from_account_number": source_number.value,
                "to_account_number": destination_number.value,
                "attempt": attempt,
            },
        )

    def _log_transfer_succeeded(
        self,
        correlation_id: UUID,
        source_account: Account,
        destination_account: Account,
        amount: Money,
        attempt: int,
    ) -> None:
        logger.info(
            "transfer_succeeded",
            extra={
                "correlation_id": str(correlation_id),
                "from_account_number": source_account.account_number.value,
                "to_account_number": destination_account.account_number.value,
                "amount_cents": amount.amount_cents,
                "currency": amount.currency,
                "from_balance_cents": source_account.balance.amount_cents,
                "to_balance_cents": destination_account.balance.amount_cents,
                "attempt": attempt,
            },
        )
