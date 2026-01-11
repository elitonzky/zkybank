from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session
from zkybank.adapters.outbound.persistence.sqlalchemy.models import AccountModel
from zkybank.application.ports.account_repository import AccountRepository
from zkybank.domain.entities.account import Account
from zkybank.domain.value_objects import AccountId, AccountNumber, Money


class SqlAlchemyAccountRepository(AccountRepository):
    def __init__(self, session: Session) -> None:
        self._session = session

    def get_by_number(self, account_number: AccountNumber) -> Account | None:
        stmt = select(AccountModel).where(AccountModel.account_number == account_number.value)
        model = self._session.execute(stmt).scalar_one_or_none()
        if model is None:
            return None
        return self._to_domain(model)

    def get_by_number_for_update(self, account_number: AccountNumber) -> Account | None:
        stmt = select(AccountModel).where(AccountModel.account_number == account_number.value)

        bind = self._session.get_bind()
        if bind is not None and bind.dialect.name != "sqlite":
            stmt = stmt.with_for_update()

        model = self._session.execute(stmt).scalar_one_or_none()
        if model is None:
            return None
        return self._to_domain(model)

    def save(self, account: Account) -> None:
        account_id_str = str(account.account_id.value)

        existing = self._session.get(AccountModel, account_id_str)
        if existing is None:
            self._session.add(
                AccountModel(
                    account_id=account_id_str,
                    account_number=account.account_number.value,
                    balance_cents=account.balance.amount_cents,
                    currency=account.balance.currency,
                )
            )
            return

        existing.account_number = account.account_number.value
        existing.balance_cents = account.balance.amount_cents
        existing.currency = account.balance.currency

    def _to_domain(self, model: AccountModel) -> Account:
        return Account(
            account_id=AccountId(value=UUID(model.account_id)),
            account_number=AccountNumber(model.account_number),
            balance=Money(amount_cents=model.balance_cents, currency=model.currency),
        )
