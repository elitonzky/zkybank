from __future__ import annotations

from zkybank.application.ports.account_repository import AccountRepository
from zkybank.application.ports.ledger_repository import LedgerRepository
from zkybank.application.ports.unit_of_work import UnitOfWork
from zkybank.domain.entities.account import Account
from zkybank.domain.entities.ledger_entry import LedgerEntry
from zkybank.domain.value_objects import AccountNumber, AccountId


class FakeAccountRepository(AccountRepository):
    """In-memory account repository for testing."""

    def __init__(self) -> None:
        self._accounts: dict[str, Account] = {}

    def get_by_number(self, account_number: AccountNumber) -> Account | None:
        return self._accounts.get(account_number.value)

    def save(self, account: Account) -> None:
        self._accounts[account.account_number.value] = account


class FakeLedgerRepository(LedgerRepository):
    """In-memory ledger repository for testing."""

    def __init__(self) -> None:
        self._entries: list[LedgerEntry] = []

    def save(self, entry: LedgerEntry) -> None:
        self._entries.append(entry)

    def list_by_account(self, account_id: AccountId) -> list[LedgerEntry]:
        return [e for e in self._entries if e.account_id == account_id]


class FakeUnitOfWork(UnitOfWork):
    """In-memory unit of work for testing."""

    def __init__(self) -> None:
        self.accounts = FakeAccountRepository()
        self.ledger = FakeLedgerRepository()
        self._committed = False

    def __enter__(self) -> FakeUnitOfWork:
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit."""
        pass

    def commit(self) -> None:
        """Mark as committed for testing verification."""
        self._committed = True

    def rollback(self) -> None:
        """Rollback (no-op in fake implementation)."""
        pass
