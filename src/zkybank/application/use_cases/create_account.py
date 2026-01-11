from __future__ import annotations

import logging

from zkybank.application.dto.commands import CreateAccountCommand
from zkybank.application.dto.results import AccountCreatedResult
from zkybank.application.errors import AccountAlreadyExistsError
from zkybank.application.ports.unit_of_work import UnitOfWork
from zkybank.domain.entities.account import Account
from zkybank.domain.entities.ledger_entry import LedgerEntry, LedgerEntryType
from zkybank.domain.value_objects import AccountNumber, Money

logger = logging.getLogger(__name__)


class CreateAccountUseCase:
    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    def execute(self, command: CreateAccountCommand) -> AccountCreatedResult:
        account_number = AccountNumber(command.account_number)
        initial_deposit_amount = Money(
            amount_cents=command.initial_balance_cents,
            currency=command.currency,
        )

        with self._uow as uow:
            self._assert_account_does_not_exist(uow, account_number)

            account = self._open_account(account_number, command.currency)

            self._apply_initial_deposit_if_any(
                uow=uow,
                account=account,
                initial_deposit_amount=initial_deposit_amount,
            )

            uow.accounts.save(account)
            uow.commit()

        self._log_account_created(account)

        return AccountCreatedResult(
            account_id=account.account_id.value,
            account_number=account.account_number.value,
            balance_cents=account.balance.amount_cents,
            currency=account.balance.currency,
        )

    def _assert_account_does_not_exist(
        self, uow: UnitOfWork, account_number: AccountNumber
    ) -> None:
        existing = uow.accounts.get_by_number(account_number)
        if existing is not None:
            raise AccountAlreadyExistsError(
                f"Account with number {account_number.value} already exists."
            )

    def _open_account(self, account_number: AccountNumber, currency: str) -> Account:
        return Account.open(account_number=account_number, currency=currency)

    def _apply_initial_deposit_if_any(
        self,
        uow: UnitOfWork,
        account: Account,
        initial_deposit_amount: Money,
    ) -> None:
        if initial_deposit_amount.is_zero():
            return

        account.deposit(initial_deposit_amount)

        uow.ledger.save(
            LedgerEntry.create(
                account_id=account.account_id,
                entry_type=LedgerEntryType.DEPOSIT,
                amount=initial_deposit_amount,
            )
        )

    def _log_account_created(self, account: Account) -> None:
        logger.info(
            "account_created",
            extra={
                "account_number": account.account_number.value,
                "currency": account.balance.currency,
                "balance_cents": account.balance.amount_cents,
            },
        )
