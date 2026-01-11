from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import sessionmaker
from zkybank.adapters.outbound.persistence.sqlalchemy.base import Base


@dataclass(frozen=True, slots=True)
class SqlAlchemySessionFactory:
    engine: Engine
    session_maker: sessionmaker


def build_session_factory(database_url: str) -> SqlAlchemySessionFactory:
    connect_args: dict[str, object] = {}
    if database_url.startswith("sqlite"):
        connect_args = {"check_same_thread": False}

    engine = create_engine(database_url, future=True, echo=False, connect_args=connect_args)
    session_maker = sessionmaker(
        bind=engine, autoflush=False, autocommit=False, expire_on_commit=False
    )

    return SqlAlchemySessionFactory(engine=engine, session_maker=session_maker)


def create_all_tables(engine: Engine) -> None:
    Base.metadata.create_all(bind=engine)
