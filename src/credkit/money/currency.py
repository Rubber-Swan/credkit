"""Currency representations for financial calculations."""

from dataclasses import dataclass
from enum import Enum


class CurrencyCode(Enum):
    """
    Supported currency codes with decimal precision.

    Currently focused on USD for consumer loan products (mortgages, auto loans, etc.).
    """

    USD = ("USD", "US Dollar", 2)

    # TODO: Add support for additional currencies as needed for international expansion.
    # Consider adding: EUR, GBP, CAD, etc. when expanding beyond US consumer loans.

    def __init__(self, code: str, name: str, decimal_places: int):
        self._code = code
        self._name = name
        self._decimal_places = decimal_places

    @property
    def code(self) -> str:
        """ISO 4217 three-letter currency code."""
        return self._code

    @property
    def display_name(self) -> str:
        """Human-readable currency name."""
        return self._name

    @property
    def decimal_places(self) -> int:
        """Standard number of decimal places for this currency."""
        return self._decimal_places

    def __str__(self) -> str:
        return self._code


@dataclass(frozen=True)
class Currency:
    """
    Represents a currency with its properties.

    Immutable value object for use in financial calculations.
    """

    code: CurrencyCode

    @classmethod
    def from_code(cls, code: str) -> "Currency":
        """
        Create a Currency from an ISO 4217 code string.

        Args:
            code: Three-letter ISO currency code (e.g., "USD")

        Returns:
            Currency instance

        Raises:
            ValueError: If the currency code is not recognized
        """
        try:
            currency_code = CurrencyCode[code.upper()]
            return cls(code=currency_code)
        except KeyError:
            raise ValueError(
                f"Unknown currency code: {code}. "
                f"Supported currencies: {', '.join(c.name for c in CurrencyCode)}"
            )

    @property
    def iso_code(self) -> str:
        """ISO 4217 three-letter currency code."""
        return self.code.code

    @property
    def name(self) -> str:
        """Human-readable currency name."""
        return self.code.display_name

    @property
    def decimal_places(self) -> int:
        """Standard number of decimal places for this currency."""
        return self.code.decimal_places

    def __str__(self) -> str:
        return self.iso_code

    def __repr__(self) -> str:
        return f"Currency({self.iso_code})"


# USD constant for convenience
USD = Currency(CurrencyCode.USD)
