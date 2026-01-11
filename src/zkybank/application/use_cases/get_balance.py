from __future__ import annotations

from zkybank.application.dto.results import BalanceResult
from zkybank.application.errors import AccountNotFoundError
from zkybank.application.ports.unit_of_work import UnitOfWork
from zkybank.domain.value_objects import AccountNumber


class GetBalanceUseCase:
    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    def execute(self, account_number: str) -> BalanceResult:
        number = AccountNumber(account_number)

        with self._uow as uow:
            account = uow.accounts.get_by_number(number)
            if account is None:
                raise AccountNotFoundError(f"Account with number {number.value} not found.")

        return BalanceResult(
            account_number=account.account_number.value,
            balance_cents=account.balance.amount_cents,
            currency=account.balance.currency,
        )
