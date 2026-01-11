from __future__ import annotations

import pytest

from zkybank.domain.entities.account import Account
from zkybank.domain.errors import InsufficientFundsError, InvalidMoneyError
from zkybank.domain.value_objects import AccountNumber, Money


class TestAccountFactory:
    """Tests for Account factory method."""

    def test_open_creates_account_with_zero_balance(self) -> None:
        """Test that open() creates an account with zero balance."""
        account_number = AccountNumber(value="123456")
        account = Account.open(account_number=account_number)

        assert account.account_number == account_number
        assert account.balance.is_zero()
        assert account.balance.currency == "BRL"

    def test_open_creates_account_with_custom_currency(self) -> None:
        """Test that open() creates an account with custom currency."""
        account_number = AccountNumber(value="123456")
        account = Account.open(account_number=account_number, currency="USD")

        assert account.balance.currency == "USD"
        assert account.balance.is_zero()

    def test_open_generates_unique_account_ids(self) -> None:
        """Test that open() generates unique account IDs."""
        account_number = AccountNumber(value="123456")
        account1 = Account.open(account_number=account_number)
        account2 = Account.open(account_number=account_number)

        assert account1.account_id != account2.account_id


class TestAccountDeposit:
    """Tests for Account deposit operations."""

    def test_deposit_increases_balance(self) -> None:
        """Test that deposit increases account balance."""
        account = Account.open(account_number=AccountNumber(value="123456"))
        deposit_amount = Money(amount_cents=1000)

        account.deposit(deposit_amount)

        assert account.balance.amount_cents == 1000

    def test_deposit_multiple_times(self) -> None:
        """Test multiple deposits accumulate correctly."""
        account = Account.open(account_number=AccountNumber(value="123456"))
        deposit1 = Money(amount_cents=1000)
        deposit2 = Money(amount_cents=500)

        account.deposit(deposit1)
        account.deposit(deposit2)

        assert account.balance.amount_cents == 1500

    def test_deposit_zero_raises_error(self) -> None:
        """Test that depositing zero raises InvalidMoneyError."""
        account = Account.open(account_number=AccountNumber(value="123456"))
        zero_amount = Money.zero()

        with pytest.raises(InvalidMoneyError, match="must be greater than zero"):
            account.deposit(zero_amount)

    def test_deposit_different_currency_raises_error(self) -> None:
        """Test that depositing different currency raises error."""
        account = Account.open(account_number=AccountNumber(value="123456"), currency="BRL")
        usd_amount = Money(amount_cents=1000, currency="USD")

        with pytest.raises(InvalidMoneyError, match="currency mismatch"):
            account.deposit(usd_amount)


class TestAccountWithdraw:
    """Tests for Account withdrawal operations."""

    def test_withdraw_decreases_balance(self) -> None:
        """Test that withdraw decreases account balance."""
        account = Account.open(account_number=AccountNumber(value="123456"))
        deposit_amount = Money(amount_cents=1000)
        withdraw_amount = Money(amount_cents=300)

        account.deposit(deposit_amount)
        account.withdraw(withdraw_amount)

        assert account.balance.amount_cents == 700

    def test_withdraw_zero_raises_error(self) -> None:
        """Test that withdrawing zero raises InvalidMoneyError."""
        account = Account.open(account_number=AccountNumber(value="123456"))

        with pytest.raises(InvalidMoneyError, match="must be greater than zero"):
            account.withdraw(Money.zero())

    def test_withdraw_insufficient_funds_raises_error(self) -> None:
        """Test that withdrawing more than balance raises error."""
        account = Account.open(account_number=AccountNumber(value="123456"))
        deposit_amount = Money(amount_cents=500)
        withdraw_amount = Money(amount_cents=1000)

        account.deposit(deposit_amount)

        with pytest.raises(InsufficientFundsError, match="Insufficient funds"):
            account.withdraw(withdraw_amount)

    def test_withdraw_entire_balance(self) -> None:
        """Test withdrawing entire balance leaves zero."""
        account = Account.open(account_number=AccountNumber(value="123456"))
        deposit_amount = Money(amount_cents=1000)

        account.deposit(deposit_amount)
        account.withdraw(deposit_amount)

        assert account.balance.is_zero()

    def test_withdraw_from_zero_balance_raises_error(self) -> None:
        """Test that withdrawing from zero balance raises error."""
        account = Account.open(account_number=AccountNumber(value="123456"))
        withdraw_amount = Money(amount_cents=100)

        with pytest.raises(InsufficientFundsError):
            account.withdraw(withdraw_amount)

    def test_withdraw_different_currency_raises_error(self) -> None:
        """Test that withdrawing different currency raises error."""
        account = Account.open(account_number=AccountNumber(value="123456"), currency="BRL")
        usd_amount = Money(amount_cents=100, currency="USD")

        with pytest.raises(InvalidMoneyError, match="currency mismatch"):
            account.withdraw(usd_amount)


class TestAccountBalance:
    """Tests for Account balance management."""

    def test_initial_balance_is_zero(self) -> None:
        """Test that new account has zero balance."""
        account = Account.open(account_number=AccountNumber(value="123456"))
        assert account.balance.is_zero()

    def test_balance_currency_matches_account_currency(self) -> None:
        """Test that balance currency matches account currency."""
        currencies = ["BRL", "USD", "EUR"]
        for currency in currencies:
            account = Account.open(account_number=AccountNumber(value="123456"), currency=currency)
            assert account.balance.currency == currency

    def test_deposit_and_withdraw_sequence(self) -> None:
        """Test complex deposit and withdraw sequence."""
        account = Account.open(account_number=AccountNumber(value="123456"))

        account.deposit(Money(amount_cents=2000))  # 2000
        account.deposit(Money(amount_cents=1500))  # 3500
        account.withdraw(Money(amount_cents=500))  # 3000
        account.withdraw(Money(amount_cents=1000))  # 2000

        assert account.balance.amount_cents == 2000

    def test_account_properties_accessible(self) -> None:
        """Test that all account properties are accessible."""
        account_number = AccountNumber(value="123456")
        account = Account.open(account_number=account_number)

        assert hasattr(account, "account_id")
        assert hasattr(account, "account_number")
        assert hasattr(account, "balance")
        assert account.account_number == account_number
