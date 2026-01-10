from __future__ import annotations

from abc import ABC, abstractmethod

from zkybank.domain.entities.account import Account
from zkybank.domain.value_objects.account_number import AccountNumber


class AccountRepository(ABC):
    """Account persistence port.

    Implementations live in outbound adapters (SQLAlchemy, in-memory, etc).
    """

    @abstractmethod
    def get_by_number(self, account_number: AccountNumber) -> Account | None:
        """Return an account by its external number, or None if not found."""
        raise NotImplementedError

    @abstractmethod
    def save(self, account: Account) -> None:
        """Persist the account state within the current unit of work."""
        raise NotImplementedError

    def get_by_number_for_update(self, account_number: AccountNumber) -> Account | None:
        """Return an account intended to be updated.

        Default implementation delegates to `get_by_number`. Database adapters may
        override to apply concurrency control (e.g., SELECT ... FOR UPDATE).
        """
        return self.get_by_number(account_number)
