from __future__ import annotations

import pytest

from zkybank.application.dto.commands import CreateAccountCommand
from zkybank.application.errors import AccountAlreadyExistsError
from zkybank.application.use_cases.create_account import CreateAccountUseCase
from tests.unit.application.fakes import FakeUnitOfWork


class TestCreateAccountUseCaseSuccess:
    """Tests for successful account creation scenarios."""

    def test_create_account_with_zero_initial_balance(self) -> None:
        """Test creating an account without initial deposit."""
        uow = FakeUnitOfWork()
        use_case = CreateAccountUseCase(uow)

        command = CreateAccountCommand(
            account_number="123456",
            initial_balance_cents=0,
        )

        result = use_case.execute(command)

        assert result.account_number == "123456"
        assert result.balance_cents == 0
        assert result.currency == "BRL"
        assert uow._committed

    def test_create_account_with_initial_balance(self) -> None:
        """Test creating an account with initial deposit."""
        uow = FakeUnitOfWork()
        use_case = CreateAccountUseCase(uow)

        command = CreateAccountCommand(
            account_number="654321",
            initial_balance_cents=5000,
            currency="BRL",
        )

        result = use_case.execute(command)

        assert result.account_number == "654321"
        assert result.balance_cents == 5000
        assert result.currency == "BRL"
        assert uow._committed

    def test_create_account_with_custom_currency(self) -> None:
        """Test creating account with different currency."""
        uow = FakeUnitOfWork()
        use_case = CreateAccountUseCase(uow)

        command = CreateAccountCommand(
            account_number="111111",
            initial_balance_cents=1000,
            currency="USD",
        )

        result = use_case.execute(command)

        assert result.currency == "USD"
        assert result.balance_cents == 1000

    def test_created_account_exists_in_repository(self) -> None:
        """Test that created account is persisted in repository."""
        uow = FakeUnitOfWork()
        use_case = CreateAccountUseCase(uow)

        command = CreateAccountCommand(
            account_number="222222",
            initial_balance_cents=2000,
        )

        result = use_case.execute(command)

        # Verify account is in repository
        from zkybank.domain.value_objects import AccountNumber

        account = uow.accounts.get_by_number(AccountNumber(value="222222"))
        assert account is not None
        assert account.account_number.value == "222222"
        assert account.balance.amount_cents == 2000

    def test_initial_deposit_creates_ledger_entry(self) -> None:
        """Test that initial deposit creates a ledger entry."""
        uow = FakeUnitOfWork()
        use_case = CreateAccountUseCase(uow)

        command = CreateAccountCommand(
            account_number="333333",
            initial_balance_cents=3000,
        )

        result = use_case.execute(command)

        # Verify ledger entry was created
        entries = uow.ledger._entries
        assert len(entries) == 1
        assert entries[0].amount.amount_cents == 3000

    def test_no_ledger_entry_for_zero_initial_balance(self) -> None:
        """Test that zero initial deposit doesn't create ledger entry."""
        uow = FakeUnitOfWork()
        use_case = CreateAccountUseCase(uow)

        command = CreateAccountCommand(
            account_number="444444",
            initial_balance_cents=0,
        )

        result = use_case.execute(command)

        # Verify no ledger entry was created
        entries = uow.ledger._entries
        assert len(entries) == 0

    def test_account_id_is_unique(self) -> None:
        """Test that each account gets a unique ID."""
        uow1 = FakeUnitOfWork()
        uow2 = FakeUnitOfWork()
        use_case1 = CreateAccountUseCase(uow1)
        use_case2 = CreateAccountUseCase(uow2)

        command = CreateAccountCommand(account_number="555555")

        result1 = use_case1.execute(command)
        result2 = use_case2.execute(command)

        assert result1.account_id != result2.account_id


class TestCreateAccountUseCaseErrors:
    """Tests for error scenarios."""

    def test_account_already_exists_error(self) -> None:
        """Test that creating duplicate account raises error."""
        uow = FakeUnitOfWork()
        use_case = CreateAccountUseCase(uow)

        command = CreateAccountCommand(account_number="666666")

        # Create first account
        use_case.execute(command)

        # Try to create duplicate
        with pytest.raises(AccountAlreadyExistsError):
            use_case.execute(command)

    def test_invalid_account_number_non_digit(self) -> None:
        """Test that invalid account number raises error."""
        uow = FakeUnitOfWork()
        use_case = CreateAccountUseCase(uow)

        command = CreateAccountCommand(account_number="123a56")

        from zkybank.domain.errors import InvalidAccountNumberError

        with pytest.raises(InvalidAccountNumberError):
            use_case.execute(command)

    def test_invalid_account_number_too_short(self) -> None:
        """Test that too-short account number raises error."""
        uow = FakeUnitOfWork()
        use_case = CreateAccountUseCase(uow)

        command = CreateAccountCommand(account_number="12345")  # Only 5 digits

        from zkybank.domain.errors import InvalidAccountNumberError

        with pytest.raises(InvalidAccountNumberError):
            use_case.execute(command)

    def test_invalid_account_number_too_long(self) -> None:
        """Test that too-long account number raises error."""
        uow = FakeUnitOfWork()
        use_case = CreateAccountUseCase(uow)

        command = CreateAccountCommand(account_number="1234567890123")  # 13 digits

        from zkybank.domain.errors import InvalidAccountNumberError

        with pytest.raises(InvalidAccountNumberError):
            use_case.execute(command)

    def test_negative_initial_balance_raises_error(self) -> None:
        """Test that negative initial balance raises error."""
        uow = FakeUnitOfWork()
        use_case = CreateAccountUseCase(uow)

        command = CreateAccountCommand(
            account_number="777777",
            initial_balance_cents=-1000,
        )

        from zkybank.domain.errors import InvalidMoneyError

        with pytest.raises(InvalidMoneyError):
            use_case.execute(command)

    def test_account_number_with_spaces_normalized(self) -> None:
        """Test that account number with spaces is normalized."""
        uow = FakeUnitOfWork()
        use_case = CreateAccountUseCase(uow)

        command = CreateAccountCommand(account_number="  123456  ")

        result = use_case.execute(command)

        # Verify it was normalized
        assert result.account_number == "123456"
        from zkybank.domain.value_objects import AccountNumber

        account = uow.accounts.get_by_number(AccountNumber(value="123456"))
        assert account is not None


class TestCreateAccountUseCaseValidation:
    """Tests for validation edge cases."""

    def test_create_with_maximum_account_number_length(self) -> None:
        """Test creating account with 12-digit number (maximum)."""
        uow = FakeUnitOfWork()
        use_case = CreateAccountUseCase(uow)

        command = CreateAccountCommand(account_number="123456789012")

        result = use_case.execute(command)
        assert result.account_number == "123456789012"

    def test_create_with_minimum_account_number_length(self) -> None:
        """Test creating account with 6-digit number (minimum)."""
        uow = FakeUnitOfWork()
        use_case = CreateAccountUseCase(uow)

        command = CreateAccountCommand(account_number="100000")

        result = use_case.execute(command)
        assert result.account_number == "100000"

    def test_create_multiple_different_accounts(self) -> None:
        """Test creating multiple accounts in same UoW."""
        uow = FakeUnitOfWork()
        use_case = CreateAccountUseCase(uow)

        cmd1 = CreateAccountCommand(account_number="111111")
        cmd2 = CreateAccountCommand(account_number="222222")
        cmd3 = CreateAccountCommand(account_number="333333")

        result1 = use_case.execute(cmd1)
        result2 = use_case.execute(cmd2)
        result3 = use_case.execute(cmd3)

        assert result1.account_number != result2.account_number
        assert result2.account_number != result3.account_number

        # All should be in repository
        from zkybank.domain.value_objects import AccountNumber

        assert uow.accounts.get_by_number(AccountNumber(value="111111")) is not None
        assert uow.accounts.get_by_number(AccountNumber(value="222222")) is not None
        assert uow.accounts.get_by_number(AccountNumber(value="333333")) is not None
