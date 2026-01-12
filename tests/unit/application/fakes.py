from __future__ import annotations

from zkybank.application.errors import ConcurrencyConflictError
from zkybank.application.ports.account_repository import AccountRepository
from zkybank.application.ports.ledger_repository import LedgerRepository
from zkybank.application.ports.unit_of_work import UnitOfWork
from zkybank.domain.entities.account import Account
from zkybank.domain.entities.ledger_entry import LedgerEntry
from zkybank.domain.value_objects import AccountId, AccountNumber


class FakeAccountRepository(AccountRepository):
    """In-memory account repository for testing."""

    def __init__(self) -> None:
        self._accounts: dict[str, Account] = {}
        self._for_update_failures_remaining: int = 0

    def set_for_update_failures(self, times: int) -> None:
        self._for_update_failures_remaining = max(0, times)

    def get_by_number(self, account_number: AccountNumber) -> Account | None:
        return self._accounts.get(account_number.value)

    def get_by_number_for_update(self, account_number: AccountNumber) -> Account | None:
        if self._for_update_failures_remaining > 0:
            self._for_update_failures_remaining -= 1
            raise ConcurrencyConflictError("Simulated concurrency conflict")
        return self.get_by_number(account_number)

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
        self._rolled_back = False

    def __enter__(self) -> "FakeUnitOfWork":
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit."""
        if exc_type is not None:
            self.rollback()

    def commit(self) -> None:
        """Mark as committed for testing verification."""
        self._committed = True

    def rollback(self) -> None:
        """Mark as rolled back for testing verification."""
        self._rolled_back = True

    def simulate_concurrency_conflicts(self, times: int) -> None:
        self.accounts.set_for_update_failures(times)
