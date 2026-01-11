from __future__ import annotations

from fastapi import FastAPI

from zkybank.adapters.inbound.http.fastapi.error_handlers import register_error_handlers
from zkybank.adapters.inbound.http.fastapi.routes import routers


def create_app() -> FastAPI:
    app = FastAPI(title="zkybank", version="0.1.0")

    for router in routers:
        app.include_router(router)

    register_error_handlers(app)
    return app
