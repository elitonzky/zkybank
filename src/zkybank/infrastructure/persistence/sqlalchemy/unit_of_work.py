from __future__ import annotations

from sqlalchemy.orm import Session, sessionmaker
from zkybank.application.ports.unit_of_work import UnitOfWork
from zkybank.infrastructure.persistence.sqlalchemy.repositories.account_repository import (
    SqlAlchemyAccountRepository,
)
from zkybank.infrastructure.persistence.sqlalchemy.repositories.ledger_repository import (
    SqlAlchemyLedgerRepository,
)


class SqlAlchemyUnitOfWork(UnitOfWork):
    def __init__(self, session_maker: sessionmaker) -> None:
        self._session_maker = session_maker
        self._session: Session | None = None

    def __enter__(self) -> "SqlAlchemyUnitOfWork":
        self._session = self._session_maker()

        self.accounts = SqlAlchemyAccountRepository(self._session)
        self.ledger = SqlAlchemyLedgerRepository(self._session)

        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        if self._session is None:
            return

        if exc_type is not None:
            self.rollback()

        self._session.close()
        self._session = None

    def commit(self) -> None:
        if self._session is None:
            raise RuntimeError("UnitOfWork has no active session.")
        self._session.commit()

    def rollback(self) -> None:
        if self._session is None:
            raise RuntimeError("UnitOfWork has no active session.")
        self._session.rollback()
