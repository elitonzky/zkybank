from __future__ import annotations

from pathlib import Path

from zkybank.adapters.outbound.persistence.sqlalchemy.session import (
    build_session_factory,
    create_all_tables,
)
from zkybank.adapters.outbound.persistence.sqlalchemy.unit_of_work import SqlAlchemyUnitOfWork
from zkybank.application.dto.commands import (
    CreateAccountCommand,
    DepositCommand,
    TransferCommand,
    WithdrawCommand,
)
from zkybank.application.use_cases.create_account import CreateAccountUseCase
from zkybank.application.use_cases.deposit import DepositUseCase
from zkybank.application.use_cases.get_balance import GetBalanceUseCase
from zkybank.application.use_cases.transfer import TransferUseCase
from zkybank.application.use_cases.withdraw import WithdrawUseCase


def _project_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _reset_sqlite_db(db_path: Path) -> None:
    candidates = [
        db_path,
        db_path.with_suffix(db_path.suffix + "-journal"),
        db_path.with_suffix(db_path.suffix + "-wal"),
        db_path.with_suffix(db_path.suffix + "-shm"),
    ]

    removed_any = False
    for file_path in candidates:
        if file_path.exists():
            file_path.unlink()
            removed_any = True

    if removed_any:
        print(f"[OK] Database reset: removed existing files for {db_path}")
    else:
        print(f"[OK] Database reset: no previous database found at {db_path}")


def main() -> None:
    print("=== ZKYBANK / SQLAlchemy + SQLite Smoke Test ===")

    project_root = _project_root()
    data_dir = project_root / "data"
    data_dir.mkdir(parents=True, exist_ok=True)

    db_path = data_dir / "zkybank.db"
    _reset_sqlite_db(db_path)

    database_url = f"sqlite:///{db_path}"
    print(f"[INFO] Using database: {database_url}")

    factory = build_session_factory(database_url)
    create_all_tables(factory.engine)
    print("[OK] Tables created")

    uow = SqlAlchemyUnitOfWork(factory.session_maker)

    print("\n[STEP] Creating accounts...")
    created_1 = CreateAccountUseCase(uow).execute(
        CreateAccountCommand(
            account_number="123456",
            initial_balance_cents=10000,
            currency="BRL",
        )
    )
    print(
        f"[OK] Account created: number={created_1.account_number} balance_cents={created_1.balance_cents}"
    )

    created_2 = CreateAccountUseCase(uow).execute(
        CreateAccountCommand(
            account_number="456789",
            initial_balance_cents=0,
            currency="BRL",
        )
    )
    print(
        f"[OK] Account created: number={created_2.account_number} balance_cents={created_2.balance_cents}"
    )

    print("\n[STEP] Deposit into account 456789 (5000 cents)...")
    deposit_result = DepositUseCase(uow).execute(
        DepositCommand(
            account_number="456789",
            amount_cents=5000,
            currency="BRL",
        )
    )
    print(
        f"[OK] Deposit applied: number={deposit_result.account_number} balance_cents={deposit_result.balance_cents}"
    )

    print("\n[STEP] Withdraw from account 123456 (2000 cents)...")
    withdraw_result = WithdrawUseCase(uow).execute(
        WithdrawCommand(
            account_number="123456",
            amount_cents=2000,
            currency="BRL",
        )
    )
    print(
        f"[OK] Withdrawal applied: number={withdraw_result.account_number} balance_cents={withdraw_result.balance_cents}"
    )

    print("\n[STEP] Transfer 3000 cents from 123456 -> 456789...")
    transfer_result = TransferUseCase(uow).execute(
        TransferCommand(
            from_account_number="123456",
            to_account_number="456789",
            amount_cents=3000,
            currency="BRL",
        )
    )
    print(
        "[OK] Transfer applied: "
        f"correlation_id={transfer_result.correlation_id} "
        f"from={transfer_result.from_account_number} "
        f"to={transfer_result.to_account_number} "
        f"from_balance_cents={transfer_result.from_balance_cents} "
        f"to_balance_cents={transfer_result.to_balance_cents}"
    )

    print("\n=== Smoke test completed successfully ===")

    print("\n[STEP] Reading balances from database (GetBalanceUseCase)...")
    balance_123 = GetBalanceUseCase(uow).execute("123456")
    balance_456 = GetBalanceUseCase(uow).execute("456789")

    print(
        f"[OK] Balance: number={balance_123.account_number} balance_cents={balance_123.balance_cents} currency={balance_123.currency}"
    )
    print(
        f"[OK] Balance: number={balance_456.account_number} balance_cents={balance_456.balance_cents} currency={balance_456.currency}"
    )


if __name__ == "__main__":
    main()
