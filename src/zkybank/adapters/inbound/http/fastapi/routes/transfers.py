from __future__ import annotations

from fastapi import APIRouter, Depends

from zkybank.adapters.inbound.http.fastapi.dependencies import get_uow
from zkybank.adapters.inbound.http.fastapi.schemas import TransferRequest, TransferResponse
from zkybank.application.dto.commands import TransferCommand
from zkybank.application.ports.unit_of_work import UnitOfWork
from zkybank.application.use_cases.transfer import TransferUseCase

router = APIRouter(prefix="/transfers", tags=["transfers"])


@router.post("", response_model=TransferResponse)
def transfer(payload: TransferRequest, uow: UnitOfWork = Depends(get_uow)) -> TransferResponse:
    result = TransferUseCase(uow).execute(
        TransferCommand(
            from_account_number=payload.from_account_number,
            to_account_number=payload.to_account_number,
            amount_cents=payload.amount_cents,
            currency=payload.currency,
        )
    )
    return TransferResponse(
        correlation_id=str(result.correlation_id),
        from_account_number=result.from_account_number,
        to_account_number=result.to_account_number,
        from_balance_cents=result.from_balance_cents,
        to_balance_cents=result.to_balance_cents,
        currency=result.currency,
    )
