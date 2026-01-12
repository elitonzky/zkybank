from __future__ import annotations

from tests.unit.application.fakes import FakeUnitOfWork
from zkybank.application.dto.commands import CreateAccountCommand, DepositCommand, WithdrawCommand
from zkybank.application.use_cases.create_account import CreateAccountUseCase
from zkybank.application.use_cases.deposit import DepositUseCase
from zkybank.application.use_cases.get_transactions import GetTransactionsUseCase
from zkybank.application.use_cases.withdraw import WithdrawUseCase
from zkybank.domain.entities.ledger_entry import LedgerEntryType


class TestGetTransactionsUseCase:
    def test_returns_account_transactions_in_reverse_chronological_order(self) -> None:
        uow = FakeUnitOfWork()

        CreateAccountUseCase(uow).execute(
            CreateAccountCommand(account_number="111111", initial_balance_cents=0, currency="BRL")
        )

        DepositUseCase(uow).execute(
            DepositCommand(account_number="111111", amount_cents=1000, currency="BRL")
        )
        WithdrawUseCase(uow).execute(
            WithdrawCommand(account_number="111111", amount_cents=200, currency="BRL")
        )

        entries = GetTransactionsUseCase(uow).execute(account_number="111111")

        assert len(entries) == 2
        assert entries[0].entry_type == LedgerEntryType.WITHDRAWAL
        assert entries[1].entry_type == LedgerEntryType.DEPOSIT
