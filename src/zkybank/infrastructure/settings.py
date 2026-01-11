from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv


@dataclass(frozen=True, slots=True)
class Settings:
    database_url: str
    log_level: str

    @staticmethod
    def from_env() -> "Settings":
        load_dotenv()

        database_url = os.getenv("DATABASE_URL", "")
        log_level = os.getenv("LOG_LEVEL", "INFO")

        return Settings(database_url=database_url, log_level=log_level)
