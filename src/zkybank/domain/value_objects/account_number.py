from __future__ import annotations

from dataclasses import dataclass

from zkybank.domain.errors import InvalidAccountNumberError


@dataclass(frozen=True, slots=True)
class AccountNumber:
    value: str

    def __post_init__(self) -> None:
        normalized_value = self.value.strip()

        if not normalized_value.isdigit():
            raise InvalidAccountNumberError("AccountNumber must contain only digits")

        if len(normalized_value) < 6 or len(normalized_value) > 12:
            raise InvalidAccountNumberError("AccountNumber must be between 6 and 12 digits long")

        object.__setattr__(self, "value", normalized_value)
