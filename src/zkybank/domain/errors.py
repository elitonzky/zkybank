from __future__ import annotations


class DomainError(Exception):
    """Base class for domain errors."""

    pass


class InvalidMoneyError(DomainError):
    """Raised when an invalid money operation is attempted."""

    pass


class InvalidAccountNumberError(DomainError):
    """Raised when an account number is invalid."""

    pass


class InsufficientFundsError(DomainError):
    """Raised when an account has insufficient funds for a transaction."""

    pass


class SameAccountTransferError(DomainError):
    """Raised when a transfer is attempted between the same account."""

    pass


class InvalidTransactionAmountError(DomainError):
    """Raised when a transaction amount is invalid (e.g., negative or zero)."""

    pass
