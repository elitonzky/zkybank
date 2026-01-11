from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from zkybank.application.errors import (
    AccountAlreadyExistsError,
    AccountNotFoundError,
    SameAccountTransferError,
)
from zkybank.domain.errors import DomainError


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(AccountAlreadyExistsError)
    async def _handle_account_already_exists(_: Request, exc: AccountAlreadyExistsError):
        return JSONResponse(status_code=409, content={"detail": str(exc)})

    @app.exception_handler(AccountNotFoundError)
    async def _handle_account_not_found(_: Request, exc: AccountNotFoundError):
        return JSONResponse(status_code=404, content={"detail": str(exc)})

    @app.exception_handler(SameAccountTransferError)
    async def _handle_same_account_transfer(_: Request, exc: SameAccountTransferError):
        return JSONResponse(status_code=400, content={"detail": str(exc)})

    @app.exception_handler(DomainError)
    async def _handle_domain_error(_: Request, exc: DomainError):
        return JSONResponse(status_code=400, content={"detail": str(exc)})
