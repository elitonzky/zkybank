from __future__ import annotations

import pytest

from zkybank.application.dto.commands import WithdrawCommand
from zkybank.application.errors import AccountNotFoundError
from zkybank.application.use_cases.withdraw import WithdrawUseCase
from zkybank.domain.entities.account import Account
from zkybank.domain.errors import InsufficientFundsError, InvalidMoneyError
from zkybank.domain.value_objects import AccountNumber, Money
from tests.unit.application.fakes import FakeUnitOfWork


class TestWithdrawUseCaseSuccess:
    """Tests for successful withdrawal scenarios."""

    def test_withdraw_from_existing_account(self) -> None:
        """Test withdrawing money from an existing account."""
        uow = FakeUnitOfWork()
        use_case = WithdrawUseCase(uow)

        account = Account.open(account_number=AccountNumber(value="123456"))
        account.deposit(Money(amount_cents=5000))
        uow.accounts.save(account)

        command = WithdrawCommand(
            account_number="123456",
            amount_cents=2000,
        )

        result = use_case.execute(command)

        assert result.account_number == "123456"
        assert result.balance_cents == 3000
        assert uow._committed

    def test_multiple_withdrawals(self) -> None:
        """Test that multiple withdrawals work correctly."""
        uow = FakeUnitOfWork()
        use_case = WithdrawUseCase(uow)

        account = Account.open(account_number=AccountNumber(value="654321"))
        account.deposit(Money(amount_cents=5000))
        uow.accounts.save(account)

        cmd1 = WithdrawCommand(account_number="654321", amount_cents=1000)
        cmd2 = WithdrawCommand(account_number="654321", amount_cents=500)

        result1 = use_case.execute(cmd1)
        result2 = use_case.execute(cmd2)

        assert result1.balance_cents == 4000
        assert result2.balance_cents == 3500

    def test_withdraw_entire_balance(self) -> None:
        """Test withdrawing the entire account balance."""
        uow = FakeUnitOfWork()
        use_case = WithdrawUseCase(uow)

        account = Account.open(account_number=AccountNumber(value="111111"))
        account.deposit(Money(amount_cents=1000))
        uow.accounts.save(account)

        command = WithdrawCommand(
            account_number="111111",
            amount_cents=1000,
        )

        result = use_case.execute(command)

        assert result.balance_cents == 0

    def test_withdraw_creates_ledger_entry(self) -> None:
        """Test that withdrawal creates a ledger entry."""
        uow = FakeUnitOfWork()
        use_case = WithdrawUseCase(uow)

        account = Account.open(account_number=AccountNumber(value="222222"))
        account.deposit(Money(amount_cents=5000))
        uow.accounts.save(account)

        command = WithdrawCommand(
            account_number="222222",
            amount_cents=2000,
        )

        use_case.execute(command)

        entries = uow.ledger._entries
        assert len(entries) == 1
        assert entries[0].amount.amount_cents == 2000

    def test_withdraw_with_custom_currency(self) -> None:
        """Test withdrawal with specific currency."""
        uow = FakeUnitOfWork()
        use_case = WithdrawUseCase(uow)

        account = Account.open(
            account_number=AccountNumber(value="333333"),
            currency="USD",
        )
        account.deposit(Money(amount_cents=5000, currency="USD"))
        uow.accounts.save(account)

        command = WithdrawCommand(
            account_number="333333",
            amount_cents=1500,
            currency="USD",
        )

        result = use_case.execute(command)

        assert result.currency == "USD"
        assert result.balance_cents == 3500

    def test_withdraw_minimum_positive_amount(self) -> None:
        """Test withdrawing minimum positive amount (1 cent)."""
        uow = FakeUnitOfWork()
        use_case = WithdrawUseCase(uow)

        account = Account.open(account_number=AccountNumber(value="444444"))
        account.deposit(Money(amount_cents=1000))
        uow.accounts.save(account)

        command = WithdrawCommand(
            account_number="444444",
            amount_cents=1,
        )

        result = use_case.execute(command)

        assert result.balance_cents == 999


class TestWithdrawUseCaseErrors:
    """Tests for error scenarios."""

    def test_withdraw_from_nonexistent_account(self) -> None:
        """Test that withdrawing from non-existent account raises error."""
        uow = FakeUnitOfWork()
        use_case = WithdrawUseCase(uow)

        command = WithdrawCommand(
            account_number="999999",
            amount_cents=1000,
        )

        with pytest.raises(AccountNotFoundError):
            use_case.execute(command)

    def test_withdraw_zero_raises_error(self) -> None:
        """Test that withdrawing zero raises error."""
        uow = FakeUnitOfWork()
        use_case = WithdrawUseCase(uow)

        account = Account.open(account_number=AccountNumber(value="555555"))
        account.deposit(Money(amount_cents=5000))
        uow.accounts.save(account)

        command = WithdrawCommand(
            account_number="555555",
            amount_cents=0,
        )

        with pytest.raises(InvalidMoneyError):
            use_case.execute(command)

    def test_withdraw_negative_raises_error(self) -> None:
        """Test that withdrawing negative amount raises error."""
        uow = FakeUnitOfWork()
        use_case = WithdrawUseCase(uow)

        account = Account.open(account_number=AccountNumber(value="666666"))
        account.deposit(Money(amount_cents=5000))
        uow.accounts.save(account)

        command = WithdrawCommand(
            account_number="666666",
            amount_cents=-500,
        )

        with pytest.raises(InvalidMoneyError):
            use_case.execute(command)

    def test_withdraw_insufficient_funds(self) -> None:
        """Test that withdrawing more than balance raises error."""
        uow = FakeUnitOfWork()
        use_case = WithdrawUseCase(uow)

        account = Account.open(account_number=AccountNumber(value="777777"))
        account.deposit(Money(amount_cents=1000))
        uow.accounts.save(account)

        command = WithdrawCommand(
            account_number="777777",
            amount_cents=2000,  # More than balance
        )

        with pytest.raises(InsufficientFundsError):
            use_case.execute(command)

    def test_withdraw_from_zero_balance(self) -> None:
        """Test that withdrawing from zero balance raises error."""
        uow = FakeUnitOfWork()
        use_case = WithdrawUseCase(uow)

        account = Account.open(account_number=AccountNumber(value="888888"))
        uow.accounts.save(account)

        command = WithdrawCommand(
            account_number="888888",
            amount_cents=100,
        )

        with pytest.raises(InsufficientFundsError):
            use_case.execute(command)

    def test_withdraw_wrong_currency_raises_error(self) -> None:
        """Test that withdrawing wrong currency raises error."""
        uow = FakeUnitOfWork()
        use_case = WithdrawUseCase(uow)

        account = Account.open(
            account_number=AccountNumber(value="111112"),
            currency="BRL",
        )
        account.deposit(Money(amount_cents=5000, currency="BRL"))
        uow.accounts.save(account)

        command = WithdrawCommand(
            account_number="111112",
            amount_cents=1000,
            currency="USD",  # Wrong currency
        )

        with pytest.raises(InvalidMoneyError):
            use_case.execute(command)

    def test_withdraw_invalid_account_number(self) -> None:
        """Test that invalid account number raises error."""
        uow = FakeUnitOfWork()
        use_case = WithdrawUseCase(uow)

        command = WithdrawCommand(
            account_number="12345",  # Too short
            amount_cents=1000,
        )

        from zkybank.domain.errors import InvalidAccountNumberError

        with pytest.raises(InvalidAccountNumberError):
            use_case.execute(command)


class TestWithdrawUseCaseEdgeCases:
    """Tests for edge cases."""

    def test_withdraw_leaves_exact_balance(self) -> None:
        """Test that withdrawal leaves correct balance."""
        uow = FakeUnitOfWork()
        use_case = WithdrawUseCase(uow)

        account = Account.open(account_number=AccountNumber(value="222211"))
        account.deposit(Money(amount_cents=7500))
        uow.accounts.save(account)

        command = WithdrawCommand(
            account_number="222211",
            amount_cents=2500,
        )

        result = use_case.execute(command)

        assert result.balance_cents == 5000

    def test_withdraw_ledger_records_correct_entry_type(self) -> None:
        """Test that ledger entry has correct type."""
        from zkybank.domain.entities.ledger_entry import LedgerEntryType

        uow = FakeUnitOfWork()
        use_case = WithdrawUseCase(uow)

        account = Account.open(account_number=AccountNumber(value="333311"))
        account.deposit(Money(amount_cents=5000))
        uow.accounts.save(account)

        command = WithdrawCommand(
            account_number="333311",
            amount_cents=1000,
        )

        use_case.execute(command)

        entries = uow.ledger._entries
        assert entries[0].entry_type == LedgerEntryType.WITHDRAWAL

    def test_multiple_withdrawals_insufficient_at_third(self) -> None:
        """Test that balance check happens for each withdrawal."""
        uow = FakeUnitOfWork()
        use_case = WithdrawUseCase(uow)

        account = Account.open(account_number=AccountNumber(value="444411"))
        account.deposit(Money(amount_cents=2000))
        uow.accounts.save(account)

        cmd1 = WithdrawCommand(account_number="444411", amount_cents=600)
        cmd2 = WithdrawCommand(account_number="444411", amount_cents=600)
        cmd3 = WithdrawCommand(account_number="444411", amount_cents=1000)  # Insufficient

        use_case.execute(cmd1)
        use_case.execute(cmd2)

        with pytest.raises(InsufficientFundsError):
            use_case.execute(cmd3)
