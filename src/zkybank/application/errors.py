from __future__ import annotations


class ApplicationError(Exception):
    """Base class for application-specific errors."""

    pass


class AccountNotFoundError(ApplicationError):
    """Raised when an account is not found."""

    pass


class AccountAlreadyExistsError(ApplicationError):
    """Raised when attempting to create an account that already exists."""

    pass


class SameAccountTransferError(ApplicationError):
    """Raised when attempting to transfer funds to the same account."""

    pass


class ConcurrencyConflictError(ApplicationError):
    """Raised when a concurrency conflict is detected."""

    pass
