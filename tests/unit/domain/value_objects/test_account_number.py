from __future__ import annotations

import pytest

from zkybank.domain.value_objects.account_number import AccountNumber
from zkybank.domain.errors import InvalidAccountNumberError


class TestAccountNumberInstantiation:
    """Tests for AccountNumber instantiation and validation."""

    def test_account_number_creation_valid(self) -> None:
        """Test creating a valid AccountNumber."""
        account_number = AccountNumber(value="123456")
        assert account_number.value == "123456"

    def test_account_number_is_frozen(self) -> None:
        """Test that AccountNumber is immutable."""
        account_number = AccountNumber(value="123456")
        with pytest.raises(AttributeError):
            account_number.value = "654321"

    def test_account_number_strips_whitespace(self) -> None:
        """Test that whitespace is stripped from account number."""
        account_number = AccountNumber(value="  123456  ")
        assert account_number.value == "123456"

    def test_account_number_with_internal_whitespace_invalid(self) -> None:
        """Test that internal whitespace makes account number invalid."""
        with pytest.raises(InvalidAccountNumberError, match="must contain only digits"):
            AccountNumber(value="1234 56")

    def test_account_number_non_digit_invalid(self) -> None:
        """Test that non-digit characters raise InvalidAccountNumberError."""
        with pytest.raises(InvalidAccountNumberError, match="must contain only digits"):
            AccountNumber(value="12345a")

    def test_account_number_with_special_chars_invalid(self) -> None:
        """Test that special characters raise InvalidAccountNumberError."""
        with pytest.raises(InvalidAccountNumberError, match="must contain only digits"):
            AccountNumber(value="123-456")

    def test_account_number_too_short(self) -> None:
        """Test that account numbers shorter than 6 digits raise error."""
        with pytest.raises(InvalidAccountNumberError, match="between 6 and 12 digits long"):
            AccountNumber(value="12345")

    def test_account_number_too_long(self) -> None:
        """Test that account numbers longer than 12 digits raise error."""
        with pytest.raises(InvalidAccountNumberError, match="between 6 and 12 digits long"):
            AccountNumber(value="1234567890123")

    def test_account_number_minimum_length(self) -> None:
        """Test account number with exactly 6 digits (minimum)."""
        account_number = AccountNumber(value="123456")
        assert len(account_number.value) == 6

    def test_account_number_maximum_length(self) -> None:
        """Test account number with exactly 12 digits (maximum)."""
        account_number = AccountNumber(value="123456789012")
        assert len(account_number.value) == 12

    def test_account_number_empty_string_invalid(self) -> None:
        """Test that empty string raises InvalidAccountNumberError."""
        with pytest.raises(InvalidAccountNumberError, match="must contain only digits"):
            AccountNumber(value="")

    def test_account_number_only_spaces_invalid(self) -> None:
        """Test that only spaces raises InvalidAccountNumberError."""
        with pytest.raises(InvalidAccountNumberError, match="must contain only digits"):
            AccountNumber(value="      ")

    def test_account_number_equality(self) -> None:
        """Test that account numbers with same value are equal."""
        account_number1 = AccountNumber(value="123456")
        account_number2 = AccountNumber(value="123456")
        assert account_number1 == account_number2

    def test_account_number_inequality(self) -> None:
        """Test that account numbers with different values are not equal."""
        account_number1 = AccountNumber(value="123456")
        account_number2 = AccountNumber(value="654321")
        assert account_number1 != account_number2
