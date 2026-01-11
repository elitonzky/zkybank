from __future__ import annotations

from zkybank.application.ports.unit_of_work import UnitOfWork
from zkybank.infrastructure.container import build_uow


def get_uow() -> UnitOfWork:
    return build_uow()
