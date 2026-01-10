from __future__ import annotations

import pytest

from zkybank.domain.value_objects.money import Money
from zkybank.domain.errors import InvalidMoneyError


class TestMoneyInstantiation:
    """Tests for Money instantiation and validation."""

    def test_money_creation_with_default_currency(self) -> None:
        """Test creating Money with default BRL currency."""
        money = Money(amount_cents=1000)
        assert money.amount_cents == 1000
        assert money.currency == "BRL"

    def test_money_creation_with_custom_currency(self) -> None:
        """Test creating Money with custom currency."""
        money = Money(amount_cents=5000, currency="USD")
        assert money.amount_cents == 5000
        assert money.currency == "USD"

    def test_money_is_frozen(self) -> None:
        """Test that Money is immutable."""
        money = Money(amount_cents=1000)
        with pytest.raises(AttributeError):
            money.amount_cents = 2000

    def test_invalid_amount_not_integer(self) -> None:
        """Test that non-integer amounts raise InvalidMoneyError."""
        with pytest.raises(InvalidMoneyError, match="Money amount must be an int"):
            Money(amount_cents=10.5)  # type: ignore

    def test_invalid_negative_amount(self) -> None:
        """Test that negative amounts raise InvalidMoneyError."""
        with pytest.raises(InvalidMoneyError, match="Money amount cannot be a bellow zero"):
            Money(amount_cents=-100)

    def test_invalid_empty_currency(self) -> None:
        """Test that empty currency string raises InvalidMoneyError."""
        with pytest.raises(InvalidMoneyError, match="Currency must be a non-empty string"):
            Money(amount_cents=1000, currency="")

    def test_invalid_non_string_currency(self) -> None:
        """Test that non-string currency raises InvalidMoneyError."""
        with pytest.raises(InvalidMoneyError, match="Currency must be a non-empty string"):
            Money(amount_cents=1000, currency=123)  # type: ignore


class TestMoneyStaticMethods:
    """Tests for Money static methods."""

    def test_zero_with_default_currency(self) -> None:
        """Test creating zero Money with default currency."""
        money = Money.zero()
        assert money.amount_cents == 0
        assert money.currency == "BRL"

    def test_zero_with_custom_currency(self) -> None:
        """Test creating zero Money with custom currency."""
        money = Money.zero(currency="USD")
        assert money.amount_cents == 0
        assert money.currency == "USD"

    def test_is_zero_true(self) -> None:
        """Test is_zero returns True for zero Money."""
        money = Money.zero()
        assert money.is_zero() is True

    def test_is_zero_false(self) -> None:
        """Test is_zero returns False for non-zero Money."""
        money = Money(amount_cents=1000)
        assert money.is_zero() is False


class TestMoneyArithmetic:
    """Tests for Money arithmetic operations."""

    def test_add_same_currency(self) -> None:
        """Test adding Money with same currency."""
        money1 = Money(amount_cents=1000, currency="BRL")
        money2 = Money(amount_cents=500, currency="BRL")
        result = money1 + money2
        assert result.amount_cents == 1500
        assert result.currency == "BRL"

    def test_add_different_currency(self) -> None:
        """Test that adding Money with different currencies raises error."""
        money1 = Money(amount_cents=1000, currency="BRL")
        money2 = Money(amount_cents=500, currency="USD")
        with pytest.raises(InvalidMoneyError, match="Money currency mismatch"):
            money1 + money2

    def test_add_zero(self) -> None:
        """Test adding zero Money."""
        money = Money(amount_cents=1000)
        zero = Money.zero()
        result = money + zero
        assert result.amount_cents == 1000

    def test_subtract_same_currency(self) -> None:
        """Test subtracting Money with same currency."""
        money1 = Money(amount_cents=1000, currency="BRL")
        money2 = Money(amount_cents=300, currency="BRL")
        result = money1 - money2
        assert result.amount_cents == 700
        assert result.currency == "BRL"

    def test_subtract_different_currency(self) -> None:
        """Test that subtracting Money with different currencies raises error."""
        money1 = Money(amount_cents=1000, currency="BRL")
        money2 = Money(amount_cents=500, currency="USD")
        with pytest.raises(InvalidMoneyError, match="Money currency mismatch"):
            money1 - money2

    def test_subtract_results_negative(self) -> None:
        """Test that subtracting results in negative raises error."""
        money1 = Money(amount_cents=500, currency="BRL")
        money2 = Money(amount_cents=1000, currency="BRL")
        with pytest.raises(InvalidMoneyError, match="Resulting Money amount cannot be negative"):
            money1 - money2

    def test_subtract_equal_amounts(self) -> None:
        """Test subtracting equal amounts results in zero."""
        money1 = Money(amount_cents=1000, currency="BRL")
        money2 = Money(amount_cents=1000, currency="BRL")
        result = money1 - money2
        assert result.is_zero()


class TestMoneyComparisons:
    """Tests for Money comparison operations."""

    def test_less_than_true(self) -> None:
        """Test less than comparison returns True."""
        money1 = Money(amount_cents=500, currency="BRL")
        money2 = Money(amount_cents=1000, currency="BRL")
        assert money1 < money2

    def test_less_than_false(self) -> None:
        """Test less than comparison returns False."""
        money1 = Money(amount_cents=1000, currency="BRL")
        money2 = Money(amount_cents=500, currency="BRL")
        assert not (money1 < money2)

    def test_less_than_equal(self) -> None:
        """Test less than with equal amounts returns False."""
        money1 = Money(amount_cents=1000, currency="BRL")
        money2 = Money(amount_cents=1000, currency="BRL")
        assert not (money1 < money2)

    def test_less_than_different_currency(self) -> None:
        """Test that less than with different currencies raises error."""
        money1 = Money(amount_cents=500, currency="BRL")
        money2 = Money(amount_cents=1000, currency="USD")
        with pytest.raises(InvalidMoneyError, match="Money currency mismatch"):
            money1 < money2

    def test_less_than_or_equal_true_less(self) -> None:
        """Test less than or equal returns True when less."""
        money1 = Money(amount_cents=500, currency="BRL")
        money2 = Money(amount_cents=1000, currency="BRL")
        assert money1 <= money2

    def test_less_than_or_equal_true_equal(self) -> None:
        """Test less than or equal returns True when equal."""
        money1 = Money(amount_cents=1000, currency="BRL")
        money2 = Money(amount_cents=1000, currency="BRL")
        assert money1 <= money2

    def test_less_than_or_equal_false(self) -> None:
        """Test less than or equal returns False when greater."""
        money1 = Money(amount_cents=1000, currency="BRL")
        money2 = Money(amount_cents=500, currency="BRL")
        assert not (money1 <= money2)

    def test_greater_than_true(self) -> None:
        """Test greater than comparison returns True."""
        money1 = Money(amount_cents=1000, currency="BRL")
        money2 = Money(amount_cents=500, currency="BRL")
        assert money1 > money2

    def test_greater_than_false(self) -> None:
        """Test greater than comparison returns False."""
        money1 = Money(amount_cents=500, currency="BRL")
        money2 = Money(amount_cents=1000, currency="BRL")
        assert not (money1 > money2)

    def test_greater_than_equal(self) -> None:
        """Test greater than with equal amounts returns False."""
        money1 = Money(amount_cents=1000, currency="BRL")
        money2 = Money(amount_cents=1000, currency="BRL")
        assert not (money1 > money2)

    def test_greater_than_different_currency(self) -> None:
        """Test that greater than with different currencies raises error."""
        money1 = Money(amount_cents=1000, currency="BRL")
        money2 = Money(amount_cents=500, currency="USD")
        with pytest.raises(InvalidMoneyError, match="Money currency mismatch"):
            money1 > money2

    def test_greater_than_or_equal_true_greater(self) -> None:
        """Test greater than or equal returns True when greater."""
        money1 = Money(amount_cents=1000, currency="BRL")
        money2 = Money(amount_cents=500, currency="BRL")
        assert money1 >= money2

    def test_greater_than_or_equal_true_equal(self) -> None:
        """Test greater than or equal returns True when equal."""
        money1 = Money(amount_cents=1000, currency="BRL")
        money2 = Money(amount_cents=1000, currency="BRL")
        assert money1 >= money2

    def test_greater_than_or_equal_false(self) -> None:
        """Test greater than or equal returns False when less."""
        money1 = Money(amount_cents=500, currency="BRL")
        money2 = Money(amount_cents=1000, currency="BRL")
        assert not (money1 >= money2)
