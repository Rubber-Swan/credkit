"""Spread representations for rate adjustments."""

from dataclasses import dataclass
from decimal import Decimal
from typing import Self

from .rate import InterestRate


@dataclass(frozen=True)
class Spread:
    """
    Represents an interest rate spread in basis points.

    Commonly used in consumer lending to represent adjustments to base rates,
    e.g., "Prime + 200 bps" for a variable-rate loan.
    """

    basis_points: Decimal
    """Spread in basis points (1 bp = 0.01%)."""

    def __post_init__(self) -> None:
        """Validate spread parameters."""
        if not isinstance(self.basis_points, Decimal):
            object.__setattr__(self, "basis_points", Decimal(str(self.basis_points)))

    @classmethod
    def from_bps(cls, bps: int | float | Decimal) -> Self:
        """
        Create a Spread from basis points.

        Args:
            bps: Spread in basis points

        Returns:
            Spread instance

        Example:
            >>> Spread.from_bps(250)  # 250 basis points = 2.5%
        """
        if not isinstance(bps, Decimal):
            bps = Decimal(str(bps))
        return cls(basis_points=bps)

    @classmethod
    def from_percent(cls, percent: float | Decimal) -> Self:
        """
        Create a Spread from a percentage.

        Args:
            percent: Spread as a percentage (e.g., 2.5 for 2.5%)

        Returns:
            Spread instance

        Example:
            >>> Spread.from_percent(2.5)  # 2.5% = 250 basis points
        """
        if isinstance(percent, float):
            percent = Decimal(str(percent))
        bps = percent * Decimal("100")
        return cls(basis_points=bps)

    @classmethod
    def from_decimal(cls, rate: Decimal | float) -> Self:
        """
        Create a Spread from a decimal rate.

        Args:
            rate: Spread as a decimal (e.g., 0.025 for 2.5%)

        Returns:
            Spread instance

        Example:
            >>> Spread.from_decimal(0.025)  # 0.025 = 2.5% = 250 bps
        """
        if isinstance(rate, float):
            rate = Decimal(str(rate))
        bps = rate * Decimal("10000")
        return cls(basis_points=bps)

    def to_decimal(self) -> Decimal:
        """Convert spread to decimal rate (e.g., 250 bps -> 0.025)."""
        return self.basis_points / Decimal("10000")

    def to_percent(self) -> Decimal:
        """Convert spread to percentage (e.g., 250 bps -> 2.5)."""
        return self.basis_points / Decimal("100")

    def apply_to(self, base_rate: InterestRate) -> InterestRate:
        """
        Apply this spread to a base rate.

        Args:
            base_rate: The base interest rate

        Returns:
            New InterestRate with spread added

        Example:
            >>> base = InterestRate.from_percent(5.0)  # 5% APR
            >>> spread = Spread.from_bps(250)  # +250 bps
            >>> adjusted = spread.apply_to(base)  # 7.5% APR
        """
        new_rate = base_rate.rate + self.to_decimal()
        return InterestRate(
            rate=new_rate,
            compounding=base_rate.compounding,
            day_count=base_rate.day_count,
        )

    # Arithmetic operations

    def __add__(self, other: Self) -> Self:
        """Add two spreads."""
        if not isinstance(other, Spread):
            return NotImplemented
        return Spread(basis_points=self.basis_points + other.basis_points)

    def __sub__(self, other: Self) -> Self:
        """Subtract two spreads."""
        if not isinstance(other, Spread):
            return NotImplemented
        return Spread(basis_points=self.basis_points - other.basis_points)

    def __mul__(self, scalar: Decimal | int | float) -> Self:
        """Multiply spread by a scalar."""
        if isinstance(scalar, (int, float)):
            scalar = Decimal(str(scalar))
        if not isinstance(scalar, Decimal):
            return NotImplemented
        return Spread(basis_points=self.basis_points * scalar)

    def __rmul__(self, scalar: Decimal | int | float) -> Self:
        """Right multiply (scalar * spread)."""
        return self.__mul__(scalar)

    def __truediv__(self, scalar: Decimal | int | float) -> Self:
        """Divide spread by a scalar."""
        if isinstance(scalar, (int, float)):
            scalar = Decimal(str(scalar))
        if not isinstance(scalar, Decimal):
            return NotImplemented
        if scalar == 0:
            raise ZeroDivisionError("Cannot divide spread by zero")
        return Spread(basis_points=self.basis_points / scalar)

    def __neg__(self) -> Self:
        """Negate the spread."""
        return Spread(basis_points=-self.basis_points)

    def __abs__(self) -> Self:
        """Absolute value of the spread."""
        return Spread(basis_points=abs(self.basis_points))

    # Comparison operations

    def __eq__(self, other: object) -> bool:
        """Check equality."""
        if not isinstance(other, Spread):
            return NotImplemented
        return self.basis_points == other.basis_points

    def __lt__(self, other: Self) -> bool:
        """Less than comparison."""
        if not isinstance(other, Spread):
            return NotImplemented
        return self.basis_points < other.basis_points

    def __le__(self, other: Self) -> bool:
        """Less than or equal comparison."""
        if not isinstance(other, Spread):
            return NotImplemented
        return self.basis_points <= other.basis_points

    def __gt__(self, other: Self) -> bool:
        """Greater than comparison."""
        if not isinstance(other, Spread):
            return NotImplemented
        return self.basis_points > other.basis_points

    def __ge__(self, other: Self) -> bool:
        """Greater than or equal comparison."""
        if not isinstance(other, Spread):
            return NotImplemented
        return self.basis_points >= other.basis_points

    # String representation

    def __str__(self) -> str:
        return f"{self.basis_points:+.2f} bps"

    def __repr__(self) -> str:
        return f"Spread({self.basis_points} bps)"
