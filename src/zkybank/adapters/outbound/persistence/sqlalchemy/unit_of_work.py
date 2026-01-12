from __future__ import annotations

from collections.abc import Callable
from types import TracebackType

from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session
from sqlalchemy.orm.exc import StaleDataError
from zkybank.adapters.outbound.persistence.sqlalchemy.repositories.account_repository import (
    SqlAlchemyAccountRepository,
)
from zkybank.adapters.outbound.persistence.sqlalchemy.repositories.ledger_repository import (
    SqlAlchemyLedgerRepository,
)
from zkybank.application.errors import ConcurrencyConflictError
from zkybank.application.ports.unit_of_work import UnitOfWork


class SqlAlchemyUnitOfWork(UnitOfWork):
    def __init__(self, session_maker: Callable[[], Session]) -> None:
        self._session_maker = session_maker
        self._session: Session | None = None

    def __enter__(self) -> "SqlAlchemyUnitOfWork":
        self._session = self._session_maker()
        self.accounts = SqlAlchemyAccountRepository(self._session)
        self.ledger = SqlAlchemyLedgerRepository(self._session)
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        try:
            if exc_type is not None:
                self.rollback()
        finally:
            if self._session is not None:
                self._session.close()
                self._session = None

    def commit(self) -> None:
        if self._session is None:
            raise RuntimeError("UnitOfWork is not active (missing __enter__)")

        try:
            self._session.commit()
        except StaleDataError as e:
            self._session.rollback()
            raise ConcurrencyConflictError("Optimistic lock conflict during commit") from e
        except OperationalError as e:
            self._session.rollback()
            msg = str(getattr(e, "orig", e)).lower()
            if "database is locked" in msg or "database is busy" in msg:
                raise ConcurrencyConflictError("Database is busy/locked during commit") from e
            raise

    def rollback(self) -> None:
        if self._session is None:
            return
        self._session.rollback()
