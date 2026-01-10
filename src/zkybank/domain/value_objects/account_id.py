from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID, uuid4


@dataclass(frozen=True, slots=True)
class AccountId:
    value: UUID

    @classmethod
    def generate(cls) -> AccountId:
        return cls(value=uuid4())
