from __future__ import annotations

import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from threading import Event
from typing import Callable

from sqlalchemy.exc import OperationalError

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

ACCOUNT_123 = "000123"
ACCOUNT_456 = "000456"
ACCOUNT_789 = "000789"


def _project_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _reset_sqlite_db(db_path: Path) -> None:
    candidates = [
        db_path,
        db_path.with_suffix(db_path.suffix + "-journal"),
        db_path.with_suffix(db_path.suffix + "-wal"),
        db_path.with_suffix(db_path.suffix + "-shm"),
    ]
    for file_path in candidates:
        if file_path.exists():
            file_path.unlink()


def _retry_sqlite_lock(fn: Callable[[], None], *, retries: int = 50, delay_s: float = 0.02) -> None:
    last_exc: Exception | None = None
    for _ in range(retries + 1):
        try:
            fn()
            return
        except OperationalError as exc:
            msg = str(exc).lower()
            if "database is locked" not in msg:
                raise
            last_exc = exc
            time.sleep(delay_s)
    raise last_exc  # pragma: no cover


def _balance(new_uow: Callable[[], SqlAlchemyUnitOfWork], account_number: str) -> int:
    result = GetBalanceUseCase(new_uow()).execute(account_number)
    return result.balance_cents


def _create_accounts(
    new_uow: Callable[[], SqlAlchemyUnitOfWork],
    *,
    a123_balance: int,
    a456_balance: int,
    a789_balance: int,
) -> None:
    CreateAccountUseCase(new_uow()).execute(
        CreateAccountCommand(
            account_number=ACCOUNT_123, initial_balance_cents=a123_balance, currency="BRL"
        )
    )
    CreateAccountUseCase(new_uow()).execute(
        CreateAccountCommand(
            account_number=ACCOUNT_456, initial_balance_cents=a456_balance, currency="BRL"
        )
    )
    CreateAccountUseCase(new_uow()).execute(
        CreateAccountCommand(
            account_number=ACCOUNT_789, initial_balance_cents=a789_balance, currency="BRL"
        )
    )


def _run_basic(new_uow: Callable[[], SqlAlchemyUnitOfWork]) -> None:
    print("\n[CASE] basic sequential operations")

    _create_accounts(new_uow, a123_balance=0, a456_balance=0, a789_balance=0)

    DepositUseCase(new_uow()).execute(
        DepositCommand(account_number=ACCOUNT_123, amount_cents=100, currency="BRL")
    )
    assert _balance(new_uow, ACCOUNT_123) == 100

    WithdrawUseCase(new_uow()).execute(
        WithdrawCommand(account_number=ACCOUNT_123, amount_cents=50, currency="BRL")
    )
    assert _balance(new_uow, ACCOUNT_123) == 50

    TransferUseCase(new_uow()).execute(
        TransferCommand(
            from_account_number=ACCOUNT_123,
            to_account_number=ACCOUNT_456,
            amount_cents=30,
            currency="BRL",
        )
    )
    assert _balance(new_uow, ACCOUNT_123) == 20
    assert _balance(new_uow, ACCOUNT_456) == 30

    print("[OK] (basic) passed")


def _run_concurrency_1(new_uow: Callable[[], SqlAlchemyUnitOfWork]) -> None:
    print(
        f"\n[CASE] Concurrency 1: deposit({ACCOUNT_123}=50) + withdraw({ACCOUNT_123}=30) in parallel => expected 20"
    )

    _create_accounts(new_uow, a123_balance=0, a456_balance=0, a789_balance=0)

    deposit_done = Event()

    def op_deposit() -> None:
        def _op() -> None:
            DepositUseCase(new_uow()).execute(
                DepositCommand(account_number=ACCOUNT_123, amount_cents=50, currency="BRL")
            )

        _retry_sqlite_lock(_op)
        deposit_done.set()

    def op_withdraw() -> None:
        deposit_done.wait()

        def _op() -> None:
            WithdrawUseCase(new_uow()).execute(
                WithdrawCommand(account_number=ACCOUNT_123, amount_cents=30, currency="BRL")
            )

        _retry_sqlite_lock(_op)

    with ThreadPoolExecutor(max_workers=2) as ex:
        f1 = ex.submit(op_deposit)
        f2 = ex.submit(op_withdraw)
        f1.result()
        f2.result()

    final_balance = _balance(new_uow, ACCOUNT_123)
    print(f"[INFO] Final balance for {ACCOUNT_123}: {final_balance}")
    assert final_balance == 20
    print("[OK] Concurrency 1 passed")


def _run_concurrency_2(new_uow: Callable[[], SqlAlchemyUnitOfWork]) -> None:
    print(
        f"\n[CASE] Concurrency 2: deposit({ACCOUNT_123}=100) + transfer({ACCOUNT_123}->{ACCOUNT_456}=50) => "
        "expected 123=50 / 456=50"
    )

    _create_accounts(new_uow, a123_balance=0, a456_balance=0, a789_balance=0)

    deposit_done = Event()

    def op_deposit() -> None:
        def _op() -> None:
            DepositUseCase(new_uow()).execute(
                DepositCommand(account_number=ACCOUNT_123, amount_cents=100, currency="BRL")
            )

        _retry_sqlite_lock(_op)
        deposit_done.set()

    def op_transfer() -> None:
        deposit_done.wait()

        def _op() -> None:
            TransferUseCase(new_uow()).execute(
                TransferCommand(
                    from_account_number=ACCOUNT_123,
                    to_account_number=ACCOUNT_456,
                    amount_cents=50,
                    currency="BRL",
                )
            )

        _retry_sqlite_lock(_op)

    with ThreadPoolExecutor(max_workers=2) as ex:
        f1 = ex.submit(op_deposit)
        f2 = ex.submit(op_transfer)
        f1.result()
        f2.result()

    b123 = _balance(new_uow, ACCOUNT_123)
    b456 = _balance(new_uow, ACCOUNT_456)
    print(f"[INFO] Final balances: {ACCOUNT_123}={b123} {ACCOUNT_456}={b456}")
    assert b123 == 50
    assert b456 == 50
    print("[OK] Concurrency 2 passed")


def _run_concurrency_3(new_uow: Callable[[], SqlAlchemyUnitOfWork]) -> None:
    print(
        f"\n[CASE] Concurrency 3: transfer({ACCOUNT_123}->{ACCOUNT_456}=20) + transfer({ACCOUNT_456}->{ACCOUNT_789}=10)"
        " => expected 123=80 / 456=10 / 789=10"
    )

    _create_accounts(new_uow, a123_balance=100, a456_balance=0, a789_balance=0)

    first_transfer_done = Event()

    def op_transfer_1() -> None:
        def _op() -> None:
            TransferUseCase(new_uow()).execute(
                TransferCommand(
                    from_account_number=ACCOUNT_123,
                    to_account_number=ACCOUNT_456,
                    amount_cents=20,
                    currency="BRL",
                )
            )

        _retry_sqlite_lock(_op)
        first_transfer_done.set()

    def op_transfer_2() -> None:
        first_transfer_done.wait()

        def _op() -> None:
            TransferUseCase(new_uow()).execute(
                TransferCommand(
                    from_account_number=ACCOUNT_456,
                    to_account_number=ACCOUNT_789,
                    amount_cents=10,
                    currency="BRL",
                )
            )

        _retry_sqlite_lock(_op)

    with ThreadPoolExecutor(max_workers=2) as ex:
        f1 = ex.submit(op_transfer_1)
        f2 = ex.submit(op_transfer_2)
        f1.result()
        f2.result()

    b123 = _balance(new_uow, ACCOUNT_123)
    b456 = _balance(new_uow, ACCOUNT_456)
    b789 = _balance(new_uow, ACCOUNT_789)
    print(f"[INFO] Final balances: {ACCOUNT_123}={b123} {ACCOUNT_456}={b456} {ACCOUNT_789}={b789}")

    assert b123 == 80
    assert b456 == 10
    assert b789 == 10
    print("[OK] Concurrency 3 passed")


def main() -> None:
    print("=== ZKYBANK / Concurrency  Table Script (SQLite) ===")

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

    def new_uow() -> SqlAlchemyUnitOfWork:
        return SqlAlchemyUnitOfWork(factory.session_maker)

    _run_basic(new_uow)

    print("\n[RESET] Recreating DB state for concurrency 1...")
    _reset_sqlite_db(db_path)
    factory = build_session_factory(database_url)
    create_all_tables(factory.engine)
    _run_concurrency_1(lambda: SqlAlchemyUnitOfWork(factory.session_maker))

    print("\n[RESET] Recreating DB state for concurrency 2...")
    _reset_sqlite_db(db_path)
    factory = build_session_factory(database_url)
    create_all_tables(factory.engine)
    _run_concurrency_2(lambda: SqlAlchemyUnitOfWork(factory.session_maker))

    print("\n[RESET] Recreating DB state for concurrency 3...")
    _reset_sqlite_db(db_path)
    factory = build_session_factory(database_url)
    create_all_tables(factory.engine)
    _run_concurrency_3(lambda: SqlAlchemyUnitOfWork(factory.session_maker))

    print("\n=== All  table scenarios passed ===")


if __name__ == "__main__":
    main()
