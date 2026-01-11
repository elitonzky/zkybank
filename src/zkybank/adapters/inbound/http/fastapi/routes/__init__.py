from __future__ import annotations

from zkybank.adapters.inbound.http.fastapi.routes.accounts import router as accounts_router
from zkybank.adapters.inbound.http.fastapi.routes.transfers import router as transfers_router

routers = [accounts_router, transfers_router]
