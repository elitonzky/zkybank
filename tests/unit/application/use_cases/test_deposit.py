from __future__ import annotations

import pytest

from tests.unit.application.fakes import FakeUnitOfWork
from zkybank.application.dto.commands import DepositCommand
from zkybank.application.errors import AccountNotFoundError, ConcurrencyConflictError
from zkybank.application.use_cases.create_account import CreateAccountCommand, CreateAccountUseCase
from zkybank.application.use_cases.deposit import DepositUseCase
from zkybank.domain.entities.account import Account
from zkybank.domain.errors import InvalidMoneyError
from zkybank.domain.value_objects import AccountNumber, Money


class TestDepositUseCaseConcurrency:
    def test_deposit_retries_on_concurrency_conflict_and_succeeds(self) -> None:
        uow = FakeUnitOfWork()

        CreateAccountUseCase(uow).execute(
            CreateAccountCommand(
                account_number="111111",
                initial_balance_cents=0,
                currency="BRL",
            )
        )

        # Reset commit/rollback flags because CreateAccountUseCase commits.
        uow._committed = False
        uow._rolled_back = False

        # Simulate one transient concurrency conflict during lock acquisition.
        uow.simulate_concurrency_conflicts(times=1)

        result = DepositUseCase(uow).execute(
            DepositCommand(
                account_number="111111",
                amount_cents=1500,
                currency="BRL",
            )
        )

        assert result.account_number == "111111"
        assert result.balance_cents == 1500
        assert uow._committed is True

    def test_deposit_fails_after_max_retries(self) -> None:
        uow = FakeUnitOfWork()

        CreateAccountUseCase(uow).execute(
            CreateAccountCommand(
                account_number="111111",
                initial_balance_cents=0,
                currency="BRL",
            )
        )

        # Reset commit/rollback flags because CreateAccountUseCase commits.
        uow._committed = False
        uow._rolled_back = False

        # Simulate persistent conflicts so all retry attempts fail.
        uow.simulate_concurrency_conflicts(times=99)

        with pytest.raises(ConcurrencyConflictError):
            DepositUseCase(uow).execute(
                DepositCommand(
                    account_number="111111",
                    amount_cents=1500,
                    currency="BRL",
                )
            )

        account = uow.accounts.get_by_number(AccountNumber(value="111111"))
        assert account is not None
        assert account.balance.amount_cents == 0
        assert uow._committed is False
        assert uow._rolled_back is True


class TestDepositUseCaseSuccess:
    """Tests for successful deposit scenarios."""

    def test_deposit_into_existing_account(self) -> None:
        """Test depositing money into an existing account."""
        uow = FakeUnitOfWork()
        use_case = DepositUseCase(uow)

        # Setup account
        account = Account.open(account_number=AccountNumber(value="123456"))
        uow.accounts.save(account)

        command = DepositCommand(
            account_number="123456",
            amount_cents=1000,
        )

        result = use_case.execute(command)

        assert result.account_number == "123456"
        assert result.balance_cents == 1000
        assert uow._committed

    def test_multiple_deposits_accumulate(self) -> None:
        """Test that multiple deposits accumulate correctly."""
        uow = FakeUnitOfWork()
        use_case = DepositUseCase(uow)

        account = Account.open(account_number=AccountNumber(value="654321"))
        uow.accounts.save(account)

        cmd1 = DepositCommand(account_number="654321", amount_cents=500)
        cmd2 = DepositCommand(account_number="654321", amount_cents=300)
        cmd3 = DepositCommand(account_number="654321", amount_cents=200)

        result1 = use_case.execute(cmd1)
        result2 = use_case.execute(cmd2)
        result3 = use_case.execute(cmd3)

        assert result1.balance_cents == 500
        assert result2.balance_cents == 800
        assert result3.balance_cents == 1000

    def test_deposit_creates_ledger_entry(self) -> None:
        """Test that deposit creates a ledger entry."""
        uow = FakeUnitOfWork()
        use_case = DepositUseCase(uow)

        account = Account.open(account_number=AccountNumber(value="111111"))
        uow.accounts.save(account)

        command = DepositCommand(
            account_number="111111",
            amount_cents=2000,
        )

        use_case.execute(command)

        entries = uow.ledger._entries
        assert len(entries) == 1
        assert entries[0].amount.amount_cents == 2000

    def test_deposit_with_custom_currency(self) -> None:
        """Test depositing with specific currency."""
        uow = FakeUnitOfWork()
        use_case = DepositUseCase(uow)

        account = Account.open(
            account_number=AccountNumber(value="222222"),
            currency="USD",
        )
        uow.accounts.save(account)

        command = DepositCommand(
            account_number="222222",
            amount_cents=1500,
            currency="USD",
        )

        result = use_case.execute(command)

        assert result.currency == "USD"
        assert result.balance_cents == 1500

    def test_deposit_large_amount(self) -> None:
        """Test depositing a large amount."""
        uow = FakeUnitOfWork()
        use_case = DepositUseCase(uow)

        account = Account.open(account_number=AccountNumber(value="333333"))
        uow.accounts.save(account)

        command = DepositCommand(
            account_number="333333",
            amount_cents=999999999,
        )

        result = use_case.execute(command)

        assert result.balance_cents == 999999999


class TestDepositUseCaseErrors:
    """Tests for error scenarios."""

    def test_deposit_to_nonexistent_account(self) -> None:
        """Test that depositing to non-existent account raises error."""
        uow = FakeUnitOfWork()
        use_case = DepositUseCase(uow)

        command = DepositCommand(
            account_number="999999",
            amount_cents=1000,
        )

        with pytest.raises(AccountNotFoundError):
            use_case.execute(command)

    def test_deposit_zero_raises_error(self) -> None:
        """Test that depositing zero raises error."""
        uow = FakeUnitOfWork()
        use_case = DepositUseCase(uow)

        account = Account.open(account_number=AccountNumber(value="444444"))
        uow.accounts.save(account)

        command = DepositCommand(
            account_number="444444",
            amount_cents=0,
        )

        with pytest.raises(InvalidMoneyError):
            use_case.execute(command)

    def test_deposit_negative_raises_error(self) -> None:
        """Test that depositing negative amount raises error."""
        uow = FakeUnitOfWork()
        use_case = DepositUseCase(uow)

        account = Account.open(account_number=AccountNumber(value="555555"))
        uow.accounts.save(account)

        command = DepositCommand(
            account_number="555555",
            amount_cents=-500,
        )

        with pytest.raises(InvalidMoneyError):
            use_case.execute(command)

    def test_deposit_wrong_currency_raises_error(self) -> None:
        """Test that depositing wrong currency raises error."""
        uow = FakeUnitOfWork()
        use_case = DepositUseCase(uow)

        account = Account.open(
            account_number=AccountNumber(value="666666"),
            currency="BRL",
        )
        uow.accounts.save(account)

        command = DepositCommand(
            account_number="666666",
            amount_cents=1000,
            currency="USD",  # Wrong currency
        )

        with pytest.raises(InvalidMoneyError):
            use_case.execute(command)

    def test_deposit_invalid_account_number(self) -> None:
        """Test that invalid account number raises error."""
        uow = FakeUnitOfWork()
        use_case = DepositUseCase(uow)

        command = DepositCommand(
            account_number="12345",  # Too short
            amount_cents=1000,
        )

        from zkybank.domain.errors import InvalidAccountNumberError

        with pytest.raises(InvalidAccountNumberError):
            use_case.execute(command)


class TestDepositUseCaseEdgeCases:
    """Tests for edge cases."""

    def test_deposit_minimum_positive_amount(self) -> None:
        """Test depositing minimum positive amount (1 cent)."""
        uow = FakeUnitOfWork()
        use_case = DepositUseCase(uow)

        account = Account.open(account_number=AccountNumber(value="777777"))
        uow.accounts.save(account)

        command = DepositCommand(
            account_number="777777",
            amount_cents=1,
        )

        result = use_case.execute(command)

        assert result.balance_cents == 1

    def test_deposit_preserves_existing_balance(self) -> None:
        """Test that deposit adds to existing balance correctly."""
        uow = FakeUnitOfWork()
        use_case = DepositUseCase(uow)

        account = Account.open(account_number=AccountNumber(value="888888"))
        account.deposit(Money(amount_cents=5000))
        uow.accounts.save(account)

        command = DepositCommand(
            account_number="888888",
            amount_cents=2000,
        )

        result = use_case.execute(command)

        assert result.balance_cents == 7000

    def test_deposit_ledger_records_correct_entry_type(self) -> None:
        """Test that ledger entry has correct type."""
        from zkybank.domain.entities.ledger_entry import LedgerEntryType

        uow = FakeUnitOfWork()
        use_case = DepositUseCase(uow)

        account = Account.open(account_number=AccountNumber(value="999999"))
        uow.accounts.save(account)

        command = DepositCommand(
            account_number="999999",
            amount_cents=1000,
        )

        use_case.execute(command)

        entries = uow.ledger._entries
        assert entries[0].entry_type == LedgerEntryType.DEPOSIT
