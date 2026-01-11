from __future__ import annotations

from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from zkybank.infrastructure.persistence.sqlalchemy.base import Base


class AccountModel(Base):
    __tablename__ = "accounts"
    __table_args__ = (
        CheckConstraint("length(account_number) >= 6", name="ck_accounts_account_number_min_len"),
        CheckConstraint("length(currency) = 3", name="ck_accounts_currency_len"),
        CheckConstraint("balance_cents >= 0", name="ck_accounts_balance_non_negative"),
    )

    account_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    account_number: Mapped[str] = mapped_column(String(12), unique=True, index=True, nullable=False)

    balance_cents: Mapped[int] = mapped_column(Integer, nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False)

    ledger_entries: Mapped[list[LedgerEntryModel]] = relationship(
        "LedgerEntryModel",
        back_populates="account",
        cascade="all, delete-orphan",
        lazy="selectin",
    )


class LedgerEntryModel(Base):
    __tablename__ = "ledger_entries"
    __table_args__ = (
        CheckConstraint("length(currency) = 3", name="ck_ledger_currency_len"),
        CheckConstraint("amount_cents >= 0", name="ck_ledger_amount_non_negative"),
    )

    entry_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    account_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("accounts.account_id"),
        nullable=False,
        index=True,
    )

    entry_type: Mapped[str] = mapped_column(String(16), nullable=False)

    amount_cents: Mapped[int] = mapped_column(Integer, nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False)

    correlation_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    account: Mapped[AccountModel] = relationship("AccountModel", back_populates="ledger_entries")
