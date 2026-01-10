from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class CreateAccountCommand:
    account_number: str
    initial_balance_cents: int = 0
    currency: str = "BRL"


@dataclass(frozen=True, slots=True)
class DepositCommand:
    account_number: str
    amount_cents: int
    currency: str = "BRL"


@dataclass(frozen=True, slots=True)
class WithdrawCommand:
    account_number: str
    amount_cents: int
    currency: str = "BRL"

@dataclass(frozen=True, slots=True)
class TransferCommand:
    from_account_number: str
    to_account_number: str
    amount_cents: int
    currency: str = "BRL"
