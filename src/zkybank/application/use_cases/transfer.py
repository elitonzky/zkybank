from __future__ import annotations

import logging
from uuid import UUID, uuid4

from zkybank.application.dto.commands import TransferCommand
from zkybank.application.dto.results import TransferResult
from zkybank.application.errors import AccountNotFoundError, SameAccountTransferError
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
            },
        )

        return TransferResult(
            correlation_id=correlation_id,
            from_account_number=source_account.account_number.value,
            to_account_number=destination_account.account_number.value,
            from_balance_cents=source_account.balance.amount_cents,
            to_balance_cents=destination_account.balance.amount_cents,
            currency=amount.currency,
        )

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
        order. This avoids deadlocks when concurrent transfers involve the same pair of
        accounts in opposite directions (e.g., 123->456 and 456->123).

        Returns:
            A tuple (lower_account, higher_account) where lower/higher refers to
            the account_number ordering and is used only for lock acquisition.
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
        """Return (source_account, destination_account) from the locked pair.

        The two accounts are fetched in a stable lock order. This method selects which
        one is the transfer source based on the requested source_number.
        """
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
            )
        )
        uow.ledger.save(
            LedgerEntry.create(
                account_id=destination_account.account_id,
                entry_type=LedgerEntryType.TRANSFER_IN,
                amount=amount,
                correlation_id=correlation_id,
            )
        )
