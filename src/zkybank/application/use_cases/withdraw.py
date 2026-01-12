from __future__ import annotations

import logging

from zkybank.application.dto.commands import WithdrawCommand
from zkybank.application.dto.results import TransactionResult
from zkybank.application.errors import AccountNotFoundError, ConcurrencyConflictError
from zkybank.application.ports.unit_of_work import UnitOfWork
from zkybank.domain.entities.account import Account
from zkybank.domain.entities.ledger_entry import LedgerEntry, LedgerEntryType
from zkybank.domain.value_objects import AccountNumber, Money

logger = logging.getLogger(__name__)


class WithdrawUseCase:
    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    def execute(self, command: WithdrawCommand) -> TransactionResult:
        account_number = AccountNumber(command.account_number)
        amount = Money(amount_cents=command.amount_cents, currency=command.currency)

        for attempt in range(3):
            try:
                with self._uow as uow:
                    account = self._load_account_for_update(uow, account_number)

                    account.withdraw(amount)
                    self._record_withdrawal(uow, account, amount)

                    uow.accounts.save(account)
                    uow.commit()

                self._log_withdraw_succeeded(account, amount, attempt + 1)

                return TransactionResult(
                    account_number=account.account_number.value,
                    balance_cents=account.balance.amount_cents,
                    currency=account.balance.currency,
                )

            except ConcurrencyConflictError:
                logger.warning(
                    "withdraw_concurrency_conflict_retry",
                    extra={"account_number": account_number.value, "attempt": attempt + 1},
                )
                continue

        raise ConcurrencyConflictError("Withdraw failed after retries")

    def _load_account_for_update(self, uow: UnitOfWork, account_number: AccountNumber) -> Account:
        account = uow.accounts.get_by_number_for_update(account_number)
        if account is None:
            raise AccountNotFoundError(f"Account with number {account_number.value} not found.")
        return account

    def _record_withdrawal(self, uow: UnitOfWork, account: Account, amount: Money) -> None:
        uow.ledger.save(
            LedgerEntry.create(
                account_id=account.account_id,
                entry_type=LedgerEntryType.WITHDRAWAL,
                amount=amount,
            )
        )

    def _log_withdraw_succeeded(self, account: Account, amount: Money, attempt: int) -> None:
        logger.info(
            "withdraw_succeeded",
            extra={
                "account_number": account.account_number.value,
                "amount_cents": amount.amount_cents,
                "currency": amount.currency,
                "balance_cents": account.balance.amount_cents,
                "attempt": attempt,
            },
        )
