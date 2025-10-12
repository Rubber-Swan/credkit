"""Time period representations for credit modeling."""

import re
from dataclasses import dataclass
from datetime import date, timedelta
from enum import Enum
from typing import Self


class TimeUnit(Enum):
    """Time units for period representation."""

    DAYS = "D"
    WEEKS = "W"
    MONTHS = "M"
    YEARS = "Y"

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True)
class Period:
    """
    Represents a time period/tenor (e.g., 3M, 6M, 1Y).

    Commonly used in credit markets to specify loan terms, payment schedules,
    and rate tenors.
    """

    length: int
    unit: TimeUnit

    def __post_init__(self) -> None:
        """Validate period parameters."""
        if self.length < 0:
            raise ValueError("Period length must be non-negative")

    @classmethod
    def from_string(cls, period_str: str) -> Self:
        """
        Parse a period from a string representation.

        Args:
            period_str: Period string like "3M", "6M", "1Y", "90D"

        Returns:
            Period instance

        Raises:
            ValueError: If string format is invalid

        Examples:
            >>> Period.from_string("3M")
            Period(length=3, unit=TimeUnit.MONTHS)
            >>> Period.from_string("1Y")
            Period(length=1, unit=TimeUnit.YEARS)
        """
        pattern = r"^(\d+)([DWMY])$"
        match = re.match(pattern, period_str.upper().strip())

        if not match:
            raise ValueError(
                f"Invalid period string: {period_str}. "
                "Expected format like '3M', '6M', '1Y', '90D'"
            )

        length_str, unit_str = match.groups()
        length = int(length_str)

        unit_map = {
            "D": TimeUnit.DAYS,
            "W": TimeUnit.WEEKS,
            "M": TimeUnit.MONTHS,
            "Y": TimeUnit.YEARS,
        }

        return cls(length=length, unit=unit_map[unit_str])

    def add_to_date(self, start_date: date) -> date:
        """
        Add this period to a date.

        Args:
            start_date: Starting date

        Returns:
            New date after adding the period

        Note:
            Month/year additions may not be exact for dates near month-end.
            For example, Jan 31 + 1M = Feb 28/29 (last day of February).
        """
        match self.unit:
            case TimeUnit.DAYS:
                return start_date + timedelta(days=self.length)
            case TimeUnit.WEEKS:
                return start_date + timedelta(weeks=self.length)
            case TimeUnit.MONTHS:
                return self._add_months(start_date, self.length)
            case TimeUnit.YEARS:
                return self._add_months(start_date, self.length * 12)

    def to_days(self, approximate: bool = True) -> int:
        """
        Convert period to days.

        Args:
            approximate: If True, use approximations (30 days/month, 365 days/year).
                        If False, raise ValueError for non-exact conversions.

        Returns:
            Number of days

        Raises:
            ValueError: If exact conversion is not possible and approximate=False
        """
        match self.unit:
            case TimeUnit.DAYS:
                return self.length
            case TimeUnit.WEEKS:
                return self.length * 7
            case TimeUnit.MONTHS:
                if not approximate:
                    raise ValueError("Cannot exactly convert months to days")
                return self.length * 30
            case TimeUnit.YEARS:
                if not approximate:
                    raise ValueError("Cannot exactly convert years to days")
                return self.length * 365

    def to_months(self, approximate: bool = True) -> float:
        """
        Convert period to months.

        Args:
            approximate: If True, use approximations for days/weeks.
                        If False, raise ValueError for non-exact conversions.

        Returns:
            Number of months as a float

        Raises:
            ValueError: If exact conversion is not possible and approximate=False
        """
        match self.unit:
            case TimeUnit.DAYS:
                if not approximate:
                    raise ValueError("Cannot exactly convert days to months")
                return self.length / 30.0
            case TimeUnit.WEEKS:
                if not approximate:
                    raise ValueError("Cannot exactly convert weeks to months")
                return self.length * 7 / 30.0
            case TimeUnit.MONTHS:
                return float(self.length)
            case TimeUnit.YEARS:
                return float(self.length * 12)

    def to_years(self, approximate: bool = True) -> float:
        """
        Convert period to years.

        Args:
            approximate: If True, use approximations.
                        If False, raise ValueError for non-exact conversions.

        Returns:
            Number of years as a float

        Raises:
            ValueError: If exact conversion is not possible and approximate=False
        """
        return self.to_months(approximate) / 12.0

    @staticmethod
    def _add_months(start_date: date, months: int) -> date:
        """
        Add months to a date, handling month-end edge cases.

        If the result would be an invalid day (e.g., Jan 31 + 1 month),
        returns the last valid day of the target month.
        """
        # Calculate target year and month
        month = start_date.month - 1 + months
        year = start_date.year + month // 12
        month = month % 12 + 1

        # Handle day overflow (e.g., Jan 31 -> Feb 31 becomes Feb 28/29)
        day = start_date.day
        while True:
            try:
                return date(year, month, day)
            except ValueError:
                day -= 1
                if day == 0:
                    raise ValueError("Invalid date calculation")

    # Comparison operators

    def __lt__(self, other: Self) -> bool:
        """Compare periods by approximate length in days."""
        if not isinstance(other, Period):
            return NotImplemented
        return self.to_days() < other.to_days()

    def __le__(self, other: Self) -> bool:
        if not isinstance(other, Period):
            return NotImplemented
        return self.to_days() <= other.to_days()

    def __gt__(self, other: Self) -> bool:
        if not isinstance(other, Period):
            return NotImplemented
        return self.to_days() > other.to_days()

    def __ge__(self, other: Self) -> bool:
        if not isinstance(other, Period):
            return NotImplemented
        return self.to_days() >= other.to_days()

    # String representation

    def __str__(self) -> str:
        return f"{self.length}{self.unit.value}"

    def __repr__(self) -> str:
        return f"Period('{self}')"


# Common period constants for convenience

ON = Period(1, TimeUnit.DAYS)  # Overnight
ONE_WEEK = Period(1, TimeUnit.WEEKS)
ONE_MONTH = Period(1, TimeUnit.MONTHS)
THREE_MONTHS = Period(3, TimeUnit.MONTHS)
SIX_MONTHS = Period(6, TimeUnit.MONTHS)
NINE_MONTHS = Period(9, TimeUnit.MONTHS)
ONE_YEAR = Period(1, TimeUnit.YEARS)
TWO_YEARS = Period(2, TimeUnit.YEARS)
THREE_YEARS = Period(3, TimeUnit.YEARS)
FIVE_YEARS = Period(5, TimeUnit.YEARS)
SEVEN_YEARS = Period(7, TimeUnit.YEARS)
TEN_YEARS = Period(10, TimeUnit.YEARS)
