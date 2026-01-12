from __future__ import annotations

from fastapi import APIRouter, Depends

from zkybank.adapters.inbound.http.fastapi.dependencies import get_uow
from zkybank.adapters.inbound.http.fastapi.schemas import (
    AccountCreatedResponse,
    BalanceResponse,
    CreateAccountRequest,
    DepositRequest,
    TransactionEntryResponse,
    TransactionResponse,
    WithdrawRequest,
)
from zkybank.application.dto.commands import (
    CreateAccountCommand,
    DepositCommand,
    WithdrawCommand,
)
from zkybank.application.ports.unit_of_work import UnitOfWork
from zkybank.application.use_cases.create_account import CreateAccountUseCase
from zkybank.application.use_cases.deposit import DepositUseCase
from zkybank.application.use_cases.get_balance import GetBalanceUseCase
from zkybank.application.use_cases.get_transactions import GetTransactionsUseCase
from zkybank.application.use_cases.withdraw import WithdrawUseCase

router = APIRouter(prefix="/accounts", tags=["accounts"])


@router.post("", response_model=AccountCreatedResponse, status_code=201)
def create_account(
    payload: CreateAccountRequest, uow: UnitOfWork = Depends(get_uow)
) -> AccountCreatedResponse:
    result = CreateAccountUseCase(uow).execute(
        CreateAccountCommand(
            account_number=payload.account_number,
            initial_balance_cents=payload.initial_balance_cents,
            currency=payload.currency,
        )
    )
    return AccountCreatedResponse(
        account_id=str(result.account_id),
        account_number=result.account_number,
        balance_cents=result.balance_cents,
        currency=result.currency,
    )


@router.get("/{account_number}/balance", response_model=BalanceResponse)
def get_balance(account_number: str, uow: UnitOfWork = Depends(get_uow)) -> BalanceResponse:
    result = GetBalanceUseCase(uow).execute(account_number=account_number)
    return BalanceResponse(
        account_number=result.account_number,
        balance_cents=result.balance_cents,
        currency=result.currency,
    )


@router.post("/{account_number}/deposit", response_model=TransactionResponse)
def deposit(
    account_number: str, payload: DepositRequest, uow: UnitOfWork = Depends(get_uow)
) -> TransactionResponse:
    result = DepositUseCase(uow).execute(
        DepositCommand(
            account_number=account_number,
            amount_cents=payload.amount_cents,
            currency=payload.currency,
        )
    )
    return TransactionResponse(
        account_number=result.account_number,
        balance_cents=result.balance_cents,
        currency=result.currency,
    )


@router.post("/{account_number}/withdraw", response_model=TransactionResponse)
def withdraw(
    account_number: str, payload: WithdrawRequest, uow: UnitOfWork = Depends(get_uow)
) -> TransactionResponse:
    result = WithdrawUseCase(uow).execute(
        WithdrawCommand(
            account_number=account_number,
            amount_cents=payload.amount_cents,
            currency=payload.currency,
        )
    )
    return TransactionResponse(
        account_number=result.account_number,
        balance_cents=result.balance_cents,
        currency=result.currency,
    )


@router.get("/{account_number}/transactions", response_model=list[TransactionEntryResponse])
def list_transactions(
    account_number: str,
    uow: UnitOfWork = Depends(get_uow),
) -> list[TransactionEntryResponse]:
    results = GetTransactionsUseCase(uow).execute(account_number=account_number)
    return [
        TransactionEntryResponse(
            entry_id=r.entry_id,
            entry_type=r.entry_type.value,
            amount_cents=r.amount_cents,
            currency=r.currency,
            correlation_id=r.correlation_id,
            counterparty_account_number=getattr(r, "counterparty_account_number", None),
            occurred_at=r.occurred_at,
        )
        for r in results
    ]
