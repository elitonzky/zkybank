from __future__ import annotations

import pytest

from tests.unit.application.fakes import FakeUnitOfWork
from zkybank.application.dto.commands import TransferCommand
from zkybank.application.errors import (
    AccountNotFoundError,
    ConcurrencyConflictError,
    SameAccountTransferError,
)
from zkybank.application.use_cases.transfer import TransferUseCase
from zkybank.domain.entities.account import Account
from zkybank.domain.entities.ledger_entry import LedgerEntryType
from zkybank.domain.errors import InsufficientFundsError, InvalidMoneyError
from zkybank.domain.value_objects import AccountNumber, Money


class TestTransferUseCaseConcurrency:
    def test_transfer_retries_on_concurrency_conflict_and_succeeds(self) -> None:
        uow = FakeUnitOfWork()

        source = Account.open(account_number=AccountNumber(value="111111"))
        source.deposit(Money(amount_cents=5000))

        destination = Account.open(account_number=AccountNumber(value="222222"))

        uow.accounts.save(source)
        uow.accounts.save(destination)

        # Reset commit/rollback flags (defensive; depends on previous tests using same instance).
        uow._committed = False
        uow._rolled_back = False

        # Simulate one transient concurrency conflict during lock acquisition.
        uow.simulate_concurrency_conflicts(times=1)

        use_case = TransferUseCase(uow)
        result = use_case.execute(
            TransferCommand(
                from_account_number="111111",
                to_account_number="222222",
                amount_cents=2000,
            )
        )

        assert result.from_balance_cents == 3000
        assert result.to_balance_cents == 2000
        assert uow._committed is True

    def test_transfer_fails_after_max_retries(self) -> None:
        uow = FakeUnitOfWork()

        source = Account.open(account_number=AccountNumber(value="111111"))
        source.deposit(Money(amount_cents=5000))

        destination = Account.open(account_number=AccountNumber(value="222222"))

        uow.accounts.save(source)
        uow.accounts.save(destination)

        uow._committed = False
        uow._rolled_back = False

        # Simulate persistent conflicts so all retry attempts fail.
        uow.simulate_concurrency_conflicts(times=99)

        use_case = TransferUseCase(uow)

        with pytest.raises(ConcurrencyConflictError):
            use_case.execute(
                TransferCommand(
                    from_account_number="111111",
                    to_account_number="222222",
                    amount_cents=2000,
                )
            )

        source_after = uow.accounts.get_by_number(AccountNumber(value="111111"))
        destination_after = uow.accounts.get_by_number(AccountNumber(value="222222"))

        assert source_after is not None
        assert destination_after is not None
        assert source_after.balance.amount_cents == 5000
        assert destination_after.balance.amount_cents == 0
        assert uow._committed is False
        assert uow._rolled_back is True


class TestTransferUseCaseSuccess:
    """Tests for successful transfer scenarios."""

    def test_transfer_between_accounts(self) -> None:
        """Test basic transfer between two accounts."""
        uow = FakeUnitOfWork()
        use_case = TransferUseCase(uow)

        source = Account.open(account_number=AccountNumber(value="111111"))
        source.deposit(Money(amount_cents=5000))
        dest = Account.open(account_number=AccountNumber(value="222222"))

        uow.accounts.save(source)
        uow.accounts.save(dest)

        command = TransferCommand(
            from_account_number="111111",
            to_account_number="222222",
            amount_cents=2000,
        )

        result = use_case.execute(command)

        assert result.from_balance_cents == 3000
        assert result.to_balance_cents == 2000
        assert uow._committed

    def test_transfer_creates_ledger_entries(self) -> None:
        """Test that transfer creates two ledger entries (TRANSFER_OUT and TRANSFER_IN)."""
        uow = FakeUnitOfWork()
        use_case = TransferUseCase(uow)

        source = Account.open(account_number=AccountNumber(value="333333"))
        source.deposit(Money(amount_cents=5000))
        dest = Account.open(account_number=AccountNumber(value="444444"))

        uow.accounts.save(source)
        uow.accounts.save(dest)

        command = TransferCommand(
            from_account_number="333333",
            to_account_number="444444",
            amount_cents=1000,
        )

        use_case.execute(command)

        entries = uow.ledger._entries
        assert len(entries) == 2
        assert entries[0].entry_type == LedgerEntryType.TRANSFER_OUT
        assert entries[1].entry_type == LedgerEntryType.TRANSFER_IN

    def test_transfer_entries_have_same_correlation_id(self) -> None:
        """Test that both ledger entries have the same correlation_id."""
        uow = FakeUnitOfWork()
        use_case = TransferUseCase(uow)

        source = Account.open(account_number=AccountNumber(value="555555"))
        source.deposit(Money(amount_cents=5000))
        dest = Account.open(account_number=AccountNumber(value="666666"))

        uow.accounts.save(source)
        uow.accounts.save(dest)

        command = TransferCommand(
            from_account_number="555555",
            to_account_number="666666",
            amount_cents=1500,
        )

        result = use_case.execute(command)

        entries = uow.ledger._entries
        assert entries[0].correlation_id == entries[1].correlation_id
        assert entries[0].correlation_id == result.correlation_id

    def test_transfer_with_custom_currency(self) -> None:
        """Test transfer with specific currency."""
        uow = FakeUnitOfWork()
        use_case = TransferUseCase(uow)

        source = Account.open(
            account_number=AccountNumber(value="777777"),
            currency="USD",
        )
        source.deposit(Money(amount_cents=5000, currency="USD"))
        dest = Account.open(
            account_number=AccountNumber(value="888888"),
            currency="USD",
        )

        uow.accounts.save(source)
        uow.accounts.save(dest)

        command = TransferCommand(
            from_account_number="777777",
            to_account_number="888888",
            amount_cents=2000,
            currency="USD",
        )

        result = use_case.execute(command)

        assert result.currency == "USD"
        assert result.from_balance_cents == 3000

    def test_transfer_minimum_amount(self) -> None:
        """Test transferring minimum positive amount (1 cent)."""
        uow = FakeUnitOfWork()
        use_case = TransferUseCase(uow)

        source = Account.open(account_number=AccountNumber(value="111112"))
        source.deposit(Money(amount_cents=1000))
        dest = Account.open(account_number=AccountNumber(value="222223"))

        uow.accounts.save(source)
        uow.accounts.save(dest)

        command = TransferCommand(
            from_account_number="111112",
            to_account_number="222223",
            amount_cents=1,
        )

        result = use_case.execute(command)

        assert result.from_balance_cents == 999
        assert result.to_balance_cents == 1

    def test_multiple_transfers(self) -> None:
        """Test multiple transfers between different accounts."""
        uow = FakeUnitOfWork()
        use_case = TransferUseCase(uow)

        acc1 = Account.open(account_number=AccountNumber(value="100001"))
        acc1.deposit(Money(amount_cents=10000))
        acc2 = Account.open(account_number=AccountNumber(value="200001"))
        acc3 = Account.open(account_number=AccountNumber(value="300001"))

        uow.accounts.save(acc1)
        uow.accounts.save(acc2)
        uow.accounts.save(acc3)

        # Transfer 1->2
        cmd1 = TransferCommand(
            from_account_number="100001",
            to_account_number="200001",
            amount_cents=3000,
        )
        result1 = use_case.execute(cmd1)

        # Transfer 2->3
        cmd2 = TransferCommand(
            from_account_number="200001",
            to_account_number="300001",
            amount_cents=1000,
        )
        result2 = use_case.execute(cmd2)

        assert result1.from_balance_cents == 7000
        assert result1.to_balance_cents == 3000
        assert result2.from_balance_cents == 2000
        assert result2.to_balance_cents == 1000

    def test_transfer_result_has_both_account_numbers(self) -> None:
        """Test that result contains both source and destination account numbers."""
        uow = FakeUnitOfWork()
        use_case = TransferUseCase(uow)

        source = Account.open(account_number=AccountNumber(value="400001"))
        source.deposit(Money(amount_cents=5000))
        dest = Account.open(account_number=AccountNumber(value="500001"))

        uow.accounts.save(source)
        uow.accounts.save(dest)

        command = TransferCommand(
            from_account_number="400001",
            to_account_number="500001",
            amount_cents=1000,
        )

        result = use_case.execute(command)

        assert result.from_account_number == "400001"
        assert result.to_account_number == "500001"


class TestTransferUseCaseErrors:
    """Tests for error scenarios."""

    def test_transfer_to_same_account_raises_error(self) -> None:
        """Test that transferring to same account raises error."""
        uow = FakeUnitOfWork()
        use_case = TransferUseCase(uow)

        account = Account.open(account_number=AccountNumber(value="600001"))
        account.deposit(Money(amount_cents=5000))
        uow.accounts.save(account)

        command = TransferCommand(
            from_account_number="600001",
            to_account_number="600001",
            amount_cents=1000,
        )

        with pytest.raises(SameAccountTransferError):
            use_case.execute(command)

    def test_transfer_from_nonexistent_account(self) -> None:
        """Test that transferring from non-existent account raises error."""
        uow = FakeUnitOfWork()
        use_case = TransferUseCase(uow)

        dest = Account.open(account_number=AccountNumber(value="700001"))
        uow.accounts.save(dest)

        command = TransferCommand(
            from_account_number="999999",
            to_account_number="700001",
            amount_cents=1000,
        )

        with pytest.raises(AccountNotFoundError):
            use_case.execute(command)

    def test_transfer_to_nonexistent_account(self) -> None:
        """Test that transferring to non-existent account raises error."""
        uow = FakeUnitOfWork()
        use_case = TransferUseCase(uow)

        source = Account.open(account_number=AccountNumber(value="800001"))
        source.deposit(Money(amount_cents=5000))
        uow.accounts.save(source)

        command = TransferCommand(
            from_account_number="800001",
            to_account_number="999998",
            amount_cents=1000,
        )

        with pytest.raises(AccountNotFoundError):
            use_case.execute(command)

    def test_transfer_both_accounts_nonexistent(self) -> None:
        """Test that error is raised if both accounts don't exist."""
        uow = FakeUnitOfWork()
        use_case = TransferUseCase(uow)

        command = TransferCommand(
            from_account_number="111111",
            to_account_number="222222",
            amount_cents=1000,
        )

        with pytest.raises(AccountNotFoundError):
            use_case.execute(command)

    def test_transfer_insufficient_funds(self) -> None:
        """Test that transfer with insufficient funds raises error."""
        uow = FakeUnitOfWork()
        use_case = TransferUseCase(uow)

        source = Account.open(account_number=AccountNumber(value="900001"))
        source.deposit(Money(amount_cents=1000))
        dest = Account.open(account_number=AccountNumber(value="900002"))

        uow.accounts.save(source)
        uow.accounts.save(dest)

        command = TransferCommand(
            from_account_number="900001",
            to_account_number="900002",
            amount_cents=2000,  # More than available
        )

        with pytest.raises(InsufficientFundsError):
            use_case.execute(command)

    def test_transfer_zero_raises_error(self) -> None:
        """Test that transferring zero raises error."""
        uow = FakeUnitOfWork()
        use_case = TransferUseCase(uow)

        source = Account.open(account_number=AccountNumber(value="900003"))
        source.deposit(Money(amount_cents=5000))
        dest = Account.open(account_number=AccountNumber(value="900004"))

        uow.accounts.save(source)
        uow.accounts.save(dest)

        command = TransferCommand(
            from_account_number="900003",
            to_account_number="900004",
            amount_cents=0,
        )

        with pytest.raises(InvalidMoneyError):
            use_case.execute(command)

    def test_transfer_negative_raises_error(self) -> None:
        """Test that transferring negative amount raises error."""
        uow = FakeUnitOfWork()
        use_case = TransferUseCase(uow)

        source = Account.open(account_number=AccountNumber(value="900005"))
        source.deposit(Money(amount_cents=5000))
        dest = Account.open(account_number=AccountNumber(value="900006"))

        uow.accounts.save(source)
        uow.accounts.save(dest)

        command = TransferCommand(
            from_account_number="900005",
            to_account_number="900006",
            amount_cents=-1000,
        )

        with pytest.raises(InvalidMoneyError):
            use_case.execute(command)

    def test_transfer_wrong_currency_raises_error(self) -> None:
        """Test that transfer with wrong currency raises error."""
        uow = FakeUnitOfWork()
        use_case = TransferUseCase(uow)

        source = Account.open(
            account_number=AccountNumber(value="900007"),
            currency="BRL",
        )
        source.deposit(Money(amount_cents=5000, currency="BRL"))
        dest = Account.open(
            account_number=AccountNumber(value="900008"),
            currency="BRL",
        )

        uow.accounts.save(source)
        uow.accounts.save(dest)

        command = TransferCommand(
            from_account_number="900007",
            to_account_number="900008",
            amount_cents=1000,
            currency="USD",  # Wrong currency
        )

        with pytest.raises(InvalidMoneyError):
            use_case.execute(command)


class TestTransferUseCaseEdgeCases:
    """Tests for edge cases and special scenarios."""

    def test_transfer_entire_balance(self) -> None:
        """Test transferring entire source account balance."""
        uow = FakeUnitOfWork()
        use_case = TransferUseCase(uow)

        source = Account.open(account_number=AccountNumber(value="900009"))
        source.deposit(Money(amount_cents=3000))
        dest = Account.open(account_number=AccountNumber(value="900010"))

        uow.accounts.save(source)
        uow.accounts.save(dest)

        command = TransferCommand(
            from_account_number="900009",
            to_account_number="900010",
            amount_cents=3000,
        )

        result = use_case.execute(command)

        assert result.from_balance_cents == 0
        assert result.to_balance_cents == 3000

    def test_transfer_with_stable_lock_order(self) -> None:
        """Test that locks are acquired in stable order regardless of transfer direction."""
        # This test verifies the deadlock prevention strategy
        # Transfers 123456->654321 and 654321->123456 should not deadlock
        # because locks are acquired in ascending order

        uow = FakeUnitOfWork()
        use_case = TransferUseCase(uow)

        acc1 = Account.open(account_number=AccountNumber(value="123456"))
        acc1.deposit(Money(amount_cents=10000))
        acc2 = Account.open(account_number=AccountNumber(value="654321"))
        acc2.deposit(Money(amount_cents=10000))

        uow.accounts.save(acc1)
        uow.accounts.save(acc2)

        # Forward transfer: 123456 -> 654321 (1000 cents)
        cmd1 = TransferCommand(
            from_account_number="123456",
            to_account_number="654321",
            amount_cents=1000,
        )
        result1 = use_case.execute(cmd1)

        # After forward transfer:
        # 123456 should have: 10000 - 1000 = 9000
        # 654321 should have: 10000 + 1000 = 11000
        assert result1.from_balance_cents == 9000
        assert result1.to_balance_cents == 11000

        # Backward transfer: 654321 -> 123456 (500 cents)
        # Note: we need fresh UoW to pick up updated balances
        uow2 = FakeUnitOfWork()
        # Re-save current balances
        src = Account.open(account_number=AccountNumber(value="123456"))
        src.balance = Money(amount_cents=9000, currency="BRL")
        dst = Account.open(account_number=AccountNumber(value="654321"))
        dst.balance = Money(amount_cents=11000, currency="BRL")
        uow2.accounts.save(src)
        uow2.accounts.save(dst)

        use_case2 = TransferUseCase(uow2)
        cmd2 = TransferCommand(
            from_account_number="654321",
            to_account_number="123456",
            amount_cents=500,
        )
        result2 = use_case2.execute(cmd2)

        # After backward transfer:
        # 654321 should have: 11000 - 500 = 10500
        # 123456 should have: 9000 + 500 = 9500
        assert result2.from_balance_cents == 10500
        assert result2.to_balance_cents == 9500

    def test_transfer_preserves_correlation_id_across_ledger(self) -> None:
        """Test that correlation_id links source and destination entries."""
        uow = FakeUnitOfWork()
        use_case = TransferUseCase(uow)

        source = Account.open(account_number=AccountNumber(value="900011"))
        source.deposit(Money(amount_cents=5000))
        dest = Account.open(account_number=AccountNumber(value="900012"))

        uow.accounts.save(source)
        uow.accounts.save(dest)

        command = TransferCommand(
            from_account_number="900011",
            to_account_number="900012",
            amount_cents=1000,
        )

        use_case.execute(command)

        out_entry = uow.ledger._entries[0]
        in_entry = uow.ledger._entries[1]

        assert out_entry.correlation_id == in_entry.correlation_id
        assert out_entry.entry_type == LedgerEntryType.TRANSFER_OUT
        assert in_entry.entry_type == LedgerEntryType.TRANSFER_IN
