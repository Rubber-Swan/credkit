"""Payment frequency definitions for credit instruments."""

from enum import Enum

from .period import Period, TimeUnit


class PaymentFrequency(Enum):
    """
    Standard payment frequencies used in credit markets.

    Each frequency includes its corresponding period and
    the number of payments per year.
    """

    ANNUAL = ("Annual", Period(1, TimeUnit.YEARS), 1)
    SEMI_ANNUAL = ("Semi-Annual", Period(6, TimeUnit.MONTHS), 2)
    QUARTERLY = ("Quarterly", Period(3, TimeUnit.MONTHS), 4)
    BI_MONTHLY = ("Bi-Monthly", Period(2, TimeUnit.MONTHS), 6)
    MONTHLY = ("Monthly", Period(1, TimeUnit.MONTHS), 12)
    BI_WEEKLY = ("Bi-Weekly", Period(2, TimeUnit.WEEKS), 26)
    WEEKLY = ("Weekly", Period(1, TimeUnit.WEEKS), 52)
    DAILY = ("Daily", Period(1, TimeUnit.DAYS), 365)
    ZERO_COUPON = ("Zero Coupon", Period(0, TimeUnit.DAYS), 0)

    def __init__(self, display_name: str, period: Period, payments_per_year: int):
        self._display_name = display_name
        self._period = period
        self._payments_per_year = payments_per_year

    @property
    def display_name(self) -> str:
        """Human-readable name of the frequency."""
        return self._display_name

    @property
    def period(self) -> Period:
        """The period between payments."""
        return self._period

    @property
    def payments_per_year(self) -> int:
        """Number of payments per year (0 for zero coupon)."""
        return self._payments_per_year

    def __str__(self) -> str:
        return self._display_name

    def __repr__(self) -> str:
        return f"PaymentFrequency.{self.name}"
