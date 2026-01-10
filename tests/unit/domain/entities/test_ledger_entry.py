from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

import pytest

from zkybank.domain.entities.ledger_entry import LedgerEntry, LedgerEntryType
from zkybank.domain.value_objects import AccountId, Money


class TestLedgerEntryFactory:
    """Tests for LedgerEntry factory method."""

    def test_create_generates_entry_id(self) -> None:
        """Test that create() generates a unique entry ID."""
        account_id = AccountId.generate()
        entry1 = LedgerEntry.create(
            account_id=account_id,
            entry_type=LedgerEntryType.DEPOSIT,
            amount=Money(amount_cents=1000),
        )
        entry2 = LedgerEntry.create(
            account_id=account_id,
            entry_type=LedgerEntryType.DEPOSIT,
            amount=Money(amount_cents=1000),
        )

        assert entry1.entry_id != entry2.entry_id
        assert isinstance(entry1.entry_id, UUID)

    def test_create_sets_timestamp(self) -> None:
        """Test that create() sets occurred_at timestamp."""
        account_id = AccountId.generate()
        before = datetime.now(timezone.utc)

        entry = LedgerEntry.create(
            account_id=account_id,
            entry_type=LedgerEntryType.DEPOSIT,
            amount=Money(amount_cents=1000),
        )

        after = datetime.now(timezone.utc)

        assert before <= entry.occurred_at <= after

    def test_create_with_explicit_timestamp(self) -> None:
        """Test that create() respects explicit occurred_at."""
        account_id = AccountId.generate()
        explicit_time = datetime(2025, 1, 1, 12, 0, 0, tzinfo=timezone.utc)

        entry = LedgerEntry.create(
            account_id=account_id,
            entry_type=LedgerEntryType.DEPOSIT,
            amount=Money(amount_cents=1000),
            occurred_at=explicit_time,
        )

        assert entry.occurred_at == explicit_time

    def test_create_without_correlation_id(self) -> None:
        """Test that create() allows None correlation_id."""
        account_id = AccountId.generate()

        entry = LedgerEntry.create(
            account_id=account_id,
            entry_type=LedgerEntryType.DEPOSIT,
            amount=Money(amount_cents=1000),
        )

        assert entry.correlation_id is None

    def test_create_with_correlation_id(self) -> None:
        """Test that create() accepts correlation_id."""
        account_id = AccountId.generate()
        from uuid import uuid4

        correlation_id = uuid4()

        entry = LedgerEntry.create(
            account_id=account_id,
            entry_type=LedgerEntryType.TRANSFER_OUT,
            amount=Money(amount_cents=1000),
            correlation_id=correlation_id,
        )

        assert entry.correlation_id == correlation_id


class TestLedgerEntryTypes:
    """Tests for LedgerEntry types."""

    def test_all_ledger_entry_types_exist(self) -> None:
        """Test that all expected entry types exist."""
        assert LedgerEntryType.DEPOSIT.value == "DEPOSIT"
        assert LedgerEntryType.WITHDRAWAL.value == "WITHDRAWAL"
        assert LedgerEntryType.TRANSFER_IN.value == "TRANSFER_IN"
        assert LedgerEntryType.TRANSFER_OUT.value == "TRANSFER_OUT"

    def test_create_with_deposit_type(self) -> None:
        """Test creating entry with DEPOSIT type."""
        account_id = AccountId.generate()

        entry = LedgerEntry.create(
            account_id=account_id,
            entry_type=LedgerEntryType.DEPOSIT,
            amount=Money(amount_cents=1000),
        )

        assert entry.entry_type == LedgerEntryType.DEPOSIT

    def test_create_with_withdrawal_type(self) -> None:
        """Test creating entry with WITHDRAWAL type."""
        account_id = AccountId.generate()

        entry = LedgerEntry.create(
            account_id=account_id,
            entry_type=LedgerEntryType.WITHDRAWAL,
            amount=Money(amount_cents=500),
        )

        assert entry.entry_type == LedgerEntryType.WITHDRAWAL

    def test_create_with_transfer_in_type(self) -> None:
        """Test creating entry with TRANSFER_IN type."""
        account_id = AccountId.generate()

        entry = LedgerEntry.create(
            account_id=account_id,
            entry_type=LedgerEntryType.TRANSFER_IN,
            amount=Money(amount_cents=2000),
        )

        assert entry.entry_type == LedgerEntryType.TRANSFER_IN

    def test_create_with_transfer_out_type(self) -> None:
        """Test creating entry with TRANSFER_OUT type."""
        account_id = AccountId.generate()

        entry = LedgerEntry.create(
            account_id=account_id,
            entry_type=LedgerEntryType.TRANSFER_OUT,
            amount=Money(amount_cents=1500),
        )

        assert entry.entry_type == LedgerEntryType.TRANSFER_OUT


class TestLedgerEntryImmutability:
    """Tests for LedgerEntry immutability."""

    def test_ledger_entry_is_frozen(self) -> None:
        """Test that LedgerEntry is immutable."""
        account_id = AccountId.generate()
        entry = LedgerEntry.create(
            account_id=account_id,
            entry_type=LedgerEntryType.DEPOSIT,
            amount=Money(amount_cents=1000),
        )

        with pytest.raises(AttributeError):
            entry.entry_id = UUID("00000000-0000-0000-0000-000000000000")

    def test_ledger_entry_amount_immutable(self) -> None:
        """Test that entry amount cannot be changed."""
        account_id = AccountId.generate()
        entry = LedgerEntry.create(
            account_id=account_id,
            entry_type=LedgerEntryType.DEPOSIT,
            amount=Money(amount_cents=1000),
        )

        with pytest.raises(AttributeError):
            entry.amount = Money(amount_cents=2000)

    def test_ledger_entry_occurred_at_immutable(self) -> None:
        """Test that occurred_at cannot be changed."""
        account_id = AccountId.generate()
        entry = LedgerEntry.create(
            account_id=account_id,
            entry_type=LedgerEntryType.DEPOSIT,
            amount=Money(amount_cents=1000),
        )

        with pytest.raises(AttributeError):
            entry.occurred_at = datetime.now(timezone.utc)


class TestLedgerEntryProperties:
    """Tests for LedgerEntry properties."""

    def test_entry_has_all_properties(self) -> None:
        """Test that entry has all expected properties."""
        account_id = AccountId.generate()
        amount = Money(amount_cents=1000)

        entry = LedgerEntry.create(
            account_id=account_id,
            entry_type=LedgerEntryType.DEPOSIT,
            amount=amount,
        )

        assert hasattr(entry, "entry_id")
        assert hasattr(entry, "account_id")
        assert hasattr(entry, "entry_type")
        assert hasattr(entry, "amount")
        assert hasattr(entry, "correlation_id")
        assert hasattr(entry, "occurred_at")

    def test_entry_properties_values(self) -> None:
        """Test that entry properties have correct values."""
        account_id = AccountId.generate()
        amount = Money(amount_cents=1500, currency="USD")
        from uuid import uuid4

        correlation_id = uuid4()
        occurred_at = datetime(2025, 6, 15, 10, 30, 0, tzinfo=timezone.utc)

        entry = LedgerEntry.create(
            account_id=account_id,
            entry_type=LedgerEntryType.TRANSFER_IN,
            amount=amount,
            correlation_id=correlation_id,
            occurred_at=occurred_at,
        )

        assert entry.account_id == account_id
        assert entry.entry_type == LedgerEntryType.TRANSFER_IN
        assert entry.amount == amount
        assert entry.correlation_id == correlation_id
        assert entry.occurred_at == occurred_at

    def test_multiple_entries_same_account_different_ids(self) -> None:
        """Test that multiple entries for same account have different IDs."""
        account_id = AccountId.generate()

        entry1 = LedgerEntry.create(
            account_id=account_id,
            entry_type=LedgerEntryType.DEPOSIT,
            amount=Money(amount_cents=1000),
        )
        entry2 = LedgerEntry.create(
            account_id=account_id,
            entry_type=LedgerEntryType.DEPOSIT,
            amount=Money(amount_cents=500),
        )

        assert entry1.account_id == entry2.account_id
        assert entry1.entry_id != entry2.entry_id
