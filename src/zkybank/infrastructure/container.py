from __future__ import annotations

from functools import lru_cache

from zkybank.adapters.outbound.persistence.sqlalchemy.session import build_session_factory
from zkybank.adapters.outbound.persistence.sqlalchemy.unit_of_work import SqlAlchemyUnitOfWork
from zkybank.infrastructure.settings import Settings


@lru_cache
def _settings() -> Settings:
    return Settings.from_env()


@lru_cache
def _session_factory():
    settings = _settings()
    return build_session_factory(settings.database_url)


def build_uow() -> SqlAlchemyUnitOfWork:
    factory = _session_factory()
    return SqlAlchemyUnitOfWork(factory.session_maker)
