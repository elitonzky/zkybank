from __future__ import annotations

from fastapi import FastAPI

from zkybank.adapters.inbound.http.fastapi.error_handlers import register_error_handlers
from zkybank.adapters.inbound.http.fastapi.routes import routers
from zkybank.adapters.outbound.persistence.sqlalchemy.session import (
    build_session_factory,
    create_all_tables,
)
from zkybank.infrastructure.settings import settings


def create_app() -> FastAPI:
    app = FastAPI(title="zkybank", version="0.1.0")

    @app.on_event("startup")
    def _startup() -> None:
        factory = build_session_factory(settings.database_url)
        create_all_tables(factory.engine)

    for router in routers:
        app.include_router(router)

    register_error_handlers(app)
    return app
