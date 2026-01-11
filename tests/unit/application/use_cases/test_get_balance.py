from __future__ import annotations

import pytest

from tests.unit.application.fakes import FakeUnitOfWork
from zkybank.application.errors import AccountNotFoundError
from zkybank.application.use_cases.get_balance import GetBalanceUseCase
from zkybank.domain.entities.account import Account
from zkybank.domain.value_objects import AccountNumber, Money


class TestGetBalanceUseCaseSuccess:
    """Tests for successful get balance scenarios."""

    def test_get_balance_for_existing_account(self) -> None:
        """Test returning current balance for an existing account."""
        uow = FakeUnitOfWork()
        use_case = GetBalanceUseCase(uow)

        account = Account.open(account_number=AccountNumber(value="123456"))
        account.deposit(Money(amount_cents=1500))
        uow.accounts.save(account)

        result = use_case.execute(account_number="123456")

        assert result.account_number == "123456"
        assert result.balance_cents == 1500
        assert result.currency == "BRL"

    def test_get_balance_returns_zero_for_new_account(self) -> None:
        """Test returning zero balance for a newly opened account."""
        uow = FakeUnitOfWork()
        use_case = GetBalanceUseCase(uow)

        account = Account.open(account_number=AccountNumber(value="654321"))
        uow.accounts.save(account)

        result = use_case.execute(account_number="654321")

        assert result.account_number == "654321"
        assert result.balance_cents == 0
        assert result.currency == "BRL"

    def test_get_balance_with_custom_currency(self) -> None:
        """Test returning balance with custom currency."""
        uow = FakeUnitOfWork()
        use_case = GetBalanceUseCase(uow)

        account = Account.open(
            account_number=AccountNumber(value="111111"),
            currency="USD",
        )
        account.deposit(Money(amount_cents=2500, currency="USD"))
        uow.accounts.save(account)

        result = use_case.execute(account_number="111111")

        assert result.account_number == "111111"
        assert result.balance_cents == 2500
        assert result.currency == "USD"


class TestGetBalanceUseCaseErrors:
    """Tests for error scenarios."""

    def test_get_balance_for_nonexistent_account_raises_error(self) -> None:
        """Test that requesting balance for non-existent account raises error."""
        uow = FakeUnitOfWork()
        use_case = GetBalanceUseCase(uow)

        with pytest.raises(AccountNotFoundError):
            use_case.execute(account_number="999999")

    def test_get_balance_with_invalid_account_number_raises_error(self) -> None:
        """Test that invalid account number is rejected by value object validation."""
        uow = FakeUnitOfWork()
        use_case = GetBalanceUseCase(uow)

        from zkybank.domain.errors import InvalidAccountNumberError

        with pytest.raises(InvalidAccountNumberError):
            use_case.execute(account_number="12345")  # Too short (per your VO rules)
