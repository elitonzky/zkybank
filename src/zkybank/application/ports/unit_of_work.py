from __future__ import annotations

from abc import ABC, abstractmethod

from zkybank.application.ports.account_repository import AccountRepository
from zkybank.application.ports.ledger_repository import LedgerRepository


class UnitOfWork(ABC):
    """Unit of Work port.

    Provides transactional boundaries and access to repositories.
    Implementations live in outbound adapters (e.g., SQLAlchemy).
    """

    accounts: AccountRepository
    ledger: LedgerRepository

    @abstractmethod
    def __enter__(self) -> "UnitOfWork":
        raise NotImplementedError

    @abstractmethod
    def __exit__(self, exc_type, exc, tb) -> None:
        raise NotImplementedError

    @abstractmethod
    def commit(self) -> None:
        """Commit the current transaction."""
        raise NotImplementedError

    @abstractmethod
    def rollback(self) -> None:
        """Rollback the current transaction."""
        raise NotImplementedError
