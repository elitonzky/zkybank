from __future__ import annotations

from uuid import UUID

import pytest

from zkybank.domain.value_objects.account_id import AccountId


class TestAccountIdInstantiation:
    """Tests for AccountId instantiation."""

    def test_account_id_creation_with_uuid(self) -> None:
        """Test creating AccountId with explicit UUID."""
        test_uuid = UUID("550e8400-e29b-41d4-a716-446655440000")
        account_id = AccountId(value=test_uuid)
        assert account_id.value == test_uuid

    def test_account_id_is_frozen(self) -> None:
        """Test that AccountId is immutable."""
        account_id = AccountId.generate()
        with pytest.raises(AttributeError):
            account_id.value = UUID("00000000-0000-0000-0000-000000000000")

    def test_account_id_generate_creates_valid_uuid(self) -> None:
        """Test that generate() creates a valid UUID."""
        account_id = AccountId.generate()
        assert isinstance(account_id.value, UUID)
        assert account_id.value.version == 4  # UUID4 is random

    def test_account_id_generate_creates_unique_ids(self) -> None:
        """Test that generate() creates different IDs each time."""
        account_id1 = AccountId.generate()
        account_id2 = AccountId.generate()
        assert account_id1.value != account_id2.value

    def test_account_id_equality(self) -> None:
        """Test that account IDs with same UUID are equal."""
        test_uuid = UUID("550e8400-e29b-41d4-a716-446655440000")
        account_id1 = AccountId(value=test_uuid)
        account_id2 = AccountId(value=test_uuid)
        assert account_id1 == account_id2

    def test_account_id_inequality(self) -> None:
        """Test that account IDs with different UUIDs are not equal."""
        account_id1 = AccountId.generate()
        account_id2 = AccountId.generate()
        assert account_id1 != account_id2
