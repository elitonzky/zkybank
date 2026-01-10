from __future__ import annotations

from dataclasses import dataclass

from zkybank.domain.errors import InvalidMoneyError


@dataclass(frozen=True, slots=True)
class Money:
    amount_cents: int
    currency: str = "BRL"

    def __post_init__(self) -> None:
        if not isinstance(self.amount_cents, int):
            raise InvalidMoneyError("Money amount must be an int")

        if self.amount_cents < 0:
            raise InvalidMoneyError("Money amount cannot be a bellow zero")
        
        if not self.currency or not isinstance(self.currency, str):
            raise InvalidMoneyError("Currency must be a non-empty string")


    @staticmethod
    def zero(currency: str = "BRL") -> Money:
        return Money(amount_cents=0, currency=currency)

    def is_zero(self) -> bool:
        return self.amount_cents == 0

    def ensure_same_currency(self, other: Money) -> None:
        if self.currency != other.currency:
            raise InvalidMoneyError("Money currency mismatch")
    
    def __add__(self, other: Money) -> Money:
        self.ensure_same_currency(other)
        return Money(amount_cents=self.amount_cents + other.amount_cents, currency=self.currency)
    
    def __sub__(self, other: Money) -> Money:
        self.ensure_same_currency(other)
        if other.amount_cents > self.amount_cents:
            raise InvalidMoneyError("Resulting Money amount cannot be negative")
        
        return Money(amount_cents=self.amount_cents - other.amount_cents, currency=self.currency)

    def __lt__(self, other: Money) -> bool:
        self.ensure_same_currency(other)
        return self.amount_cents < other.amount_cents
    
    def __le__(self, other: Money) -> bool:
        self.ensure_same_currency(other)
        return self.amount_cents <= other.amount_cents
    
    def __gt__(self, other: Money) -> bool:
        self.ensure_same_currency(other)
        return self.amount_cents > other.amount_cents
    
    def __ge__(self, other: Money) -> bool:
        self.ensure_same_currency(other)
        return self.amount_cents >= other.amount_cents
