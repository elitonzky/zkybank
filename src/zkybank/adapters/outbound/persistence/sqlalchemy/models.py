from __future__ import annotations

from datetime import datetime
from uuid import uuid4

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from zkybank.adapters.outbound.persistence.sqlalchemy.base import Base


class AccountModel(Base):
    __tablename__ = "accounts"
    __table_args__ = (
        CheckConstraint("length(account_number) >= 6", name="ck_accounts_account_number_min_len"),
        CheckConstraint("length(account_number) <= 12", name="ck_accounts_account_number_max_len"),
        CheckConstraint("length(currency) = 3", name="ck_accounts_currency_len"),
        CheckConstraint("balance_cents >= 0", name="ck_accounts_balance_non_negative"),
    )

    account_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    account_number: Mapped[str] = mapped_column(String(12), unique=True, index=True, nullable=False)
    balance_cents: Mapped[int] = mapped_column(Integer, nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False)

    # Optimistic concurrency control (OCC)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    ledger_entries: Mapped[list["LedgerEntryModel"]] = relationship(
        "LedgerEntryModel",
        back_populates="account",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    __mapper_args__ = {"version_id_col": version}


class LedgerEntryModel(Base):
    __tablename__ = "ledger_entries"
    __table_args__ = (CheckConstraint("amount_cents > 0", name="ck_ledger_amount_positive"),)

    entry_id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid4())
    )
    account_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("accounts.account_id"), index=True, nullable=False
    )
    entry_type: Mapped[str] = mapped_column(String(32), nullable=False)
    amount_cents: Mapped[int] = mapped_column(Integer, nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False)
    correlation_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    account: Mapped[AccountModel] = relationship("AccountModel", back_populates="ledger_entries")
