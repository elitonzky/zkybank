from __future__ import annotations

from abc import ABC, abstractmethod

from zkybank.domain.entities.ledger_entry import LedgerEntry
from zkybank.domain.value_objects.account_id import AccountId


class LedgerRepository(ABC):

    @abstractmethod
    def save(self, entry: LedgerEntry) -> None:
        """Append a new ledger entry"""
        raise NotImplementedError
    
    @abstractmethod
    def list_by_account(self, account_id: AccountId) -> list[LedgerEntry]:
        """List all ledger entries for a given account"""
        raise NotImplementedError
