from __future__ import annotations

from dataclasses import dataclass

from zkybank.domain.errors import InsufficientFundsError, InvalidMoneyError
from zkybank.domain.value_objects import AccountId, AccountNumber, Money


@dataclass(slots=True)
class Account:
    account_id: AccountId
    account_number: AccountNumber
    balance: Money

    @staticmethod
    def open(account_number: AccountNumber, currency: str = "BRL") -> "Account":
        """Factory method to open a new account with zero balance."""
        return Account(
            account_id=AccountId.generate(),
            account_number=account_number,
            balance=Money.zero(currency=currency),
        )

    def deposit(self, amount: Money) -> None:
        """Deposit money into the account."""
        if amount.is_zero():
            raise InvalidMoneyError("Deposit amount must be greater than zero")

        self.balance = self.balance + amount

    def withdraw(self, amount: Money) -> None:
        """Withdraw money from the account."""
        if amount.is_zero():
            raise InvalidMoneyError("Withdrawal amount must be greater than zero")

        if amount > self.balance:
            raise InsufficientFundsError("Insufficient funds for withdrawal")
        
        self.balance = self.balance - amount
