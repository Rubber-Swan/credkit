"""Amortization schedule generation for loan instruments."""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from enum import Enum

from ..cashflow import CashFlow, CashFlowSchedule, CashFlowType
from ..money import Money
from ..temporal import BusinessDayCalendar, BusinessDayConvention, PaymentFrequency


class AmortizationType(Enum):
    """
    Types of loan amortization structures.

    Defines how principal and interest are paid over the life of a loan.
    """

    LEVEL_PAYMENT = "Level Payment"
    """
    Fixed payment amount each period, with declining interest and increasing principal.
    Most common for mortgages and auto loans.
    """

    LEVEL_PRINCIPAL = "Level Principal"
    """
    Fixed principal payment each period, with declining interest and total payment.
    Common in some commercial loans.
    """

    INTEREST_ONLY = "Interest Only"
    """
    Interest-only payments with full principal due at maturity (balloon payment).
    Common for construction loans and bridge financing.
    """

    BULLET = "Bullet"
    """
    Single payment of principal and all accrued interest at maturity.
    Zero payments during loan term.
    """

    def __str__(self) -> str:
        return self.value


def calculate_level_payment(
    principal: Money,
    periodic_rate: Decimal,
    num_payments: int,
) -> Money:
    """
    Calculate the level payment amount for an amortizing loan.

    Uses the standard annuity formula:
    PMT = P * [r(1+r)^n] / [(1+r)^n - 1]

    Args:
        principal: Loan principal amount
        periodic_rate: Interest rate per payment period (as decimal)
        num_payments: Total number of payments

    Returns:
        Payment amount per period

    Example:
        >>> principal = Money.from_float(100000)
        >>> rate = Decimal("0.005")  # 0.5% per month
        >>> payments = 360  # 30 years monthly
        >>> payment = calculate_level_payment(principal, rate, payments)
        >>> # Returns approximately $599.55
    """
    if num_payments <= 0:
        raise ValueError(f"Number of payments must be positive, got {num_payments}")

    if periodic_rate == 0:
        # No interest, just divide principal evenly
        return principal / num_payments

    if periodic_rate < 0:
        raise ValueError(f"Periodic rate must be non-negative, got {periodic_rate}")

    # PMT = P * [r(1+r)^n] / [(1+r)^n - 1]
    one_plus_r = Decimal("1") + periodic_rate
    factor = one_plus_r ** num_payments
    numerator = periodic_rate * factor
    denominator = factor - Decimal("1")

    payment_amount = principal.amount * (numerator / denominator)
    return Money(amount=payment_amount, currency=principal.currency)


def generate_payment_dates(
    start_date: date,
    frequency: PaymentFrequency,
    num_payments: int,
    calendar: BusinessDayCalendar | None = None,
    convention: BusinessDayConvention = BusinessDayConvention.MODIFIED_FOLLOWING,
) -> list[date]:
    """
    Generate a list of payment dates.

    Args:
        start_date: First payment date (unadjusted)
        frequency: Payment frequency
        num_payments: Number of payments to generate
        calendar: Business day calendar for adjustments (optional)
        convention: Business day convention for adjustments

    Returns:
        List of payment dates

    Example:
        >>> dates = generate_payment_dates(
        ...     date(2024, 2, 15),
        ...     PaymentFrequency.MONTHLY,
        ...     12,
        ... )
        >>> len(dates)
        12
    """
    if num_payments <= 0:
        return []

    dates: list[date] = []
    current_date = start_date

    for _ in range(num_payments):
        # Adjust for business days if calendar provided
        if calendar is not None:
            adjusted_date = calendar.adjust(current_date, convention)
        else:
            adjusted_date = current_date

        dates.append(adjusted_date)

        # Move to next payment date
        current_date = frequency.period.add_to_date(current_date)

    return dates


def generate_level_payment_schedule(
    principal: Money,
    periodic_rate: Decimal,
    num_payments: int,
    payment_dates: list[date],
    payment_amount: Money,
) -> CashFlowSchedule:
    """
    Generate amortization schedule for level payment loans.

    Creates separate cash flows for principal and interest portions of each payment.
    The payment amount remains constant, but the split between principal and interest
    changes over time (declining interest, increasing principal).

    Args:
        principal: Initial loan principal
        periodic_rate: Interest rate per payment period
        num_payments: Total number of payments
        payment_dates: List of payment dates
        payment_amount: Fixed payment amount per period

    Returns:
        CashFlowSchedule with PRINCIPAL and INTEREST flows

    Example:
        >>> principal = Money.from_float(100000)
        >>> rate = Decimal("0.005")
        >>> dates = [date(2024, i, 1) for i in range(1, 13)]
        >>> payment = calculate_level_payment(principal, rate, 12)
        >>> schedule = generate_level_payment_schedule(principal, rate, 12, dates, payment)
    """
    if len(payment_dates) != num_payments:
        raise ValueError(
            f"Number of payment dates ({len(payment_dates)}) must match "
            f"number of payments ({num_payments})"
        )

    cash_flows: list[CashFlow] = []
    outstanding_balance = principal.amount

    for i, payment_date in enumerate(payment_dates):
        # Calculate interest for this period
        interest_amount = outstanding_balance * periodic_rate
        interest = Money(amount=interest_amount, currency=principal.currency)

        # Calculate principal portion
        # For last payment, use remaining balance to avoid rounding errors
        if i == num_payments - 1:
            principal_amount = outstanding_balance
        else:
            principal_amount = payment_amount.amount - interest_amount

        principal_payment = Money(amount=principal_amount, currency=principal.currency)

        # Create cash flows
        cash_flows.append(
            CashFlow(
                date=payment_date,
                amount=interest,
                type=CashFlowType.INTEREST,
                description=f"Payment {i+1}/{num_payments} - Interest"
            )
        )

        cash_flows.append(
            CashFlow(
                date=payment_date,
                amount=principal_payment,
                type=CashFlowType.PRINCIPAL,
                description=f"Payment {i+1}/{num_payments} - Principal"
            )
        )

        # Update outstanding balance
        outstanding_balance -= principal_amount

    return CashFlowSchedule.from_list(cash_flows, sort=True)


def generate_level_principal_schedule(
    principal: Money,
    periodic_rate: Decimal,
    num_payments: int,
    payment_dates: list[date],
) -> CashFlowSchedule:
    """
    Generate amortization schedule with fixed principal payments.

    Each payment includes a fixed principal amount plus interest on the outstanding
    balance. Total payment declines over time as interest declines.

    Args:
        principal: Initial loan principal
        periodic_rate: Interest rate per payment period
        num_payments: Total number of payments
        payment_dates: List of payment dates

    Returns:
        CashFlowSchedule with PRINCIPAL and INTEREST flows

    Example:
        >>> principal = Money.from_float(120000)
        >>> rate = Decimal("0.005")
        >>> dates = [date(2024, i, 1) for i in range(1, 13)]
        >>> schedule = generate_level_principal_schedule(principal, rate, 12, dates)
    """
    if len(payment_dates) != num_payments:
        raise ValueError(
            f"Number of payment dates ({len(payment_dates)}) must match "
            f"number of payments ({num_payments})"
        )

    cash_flows: list[CashFlow] = []

    # Fixed principal per payment
    principal_per_payment = principal.amount / num_payments
    outstanding_balance = principal.amount

    for i, payment_date in enumerate(payment_dates):
        # Calculate interest on outstanding balance
        interest_amount = outstanding_balance * periodic_rate
        interest = Money(amount=interest_amount, currency=principal.currency)

        # Fixed principal payment (use remaining balance on last payment)
        if i == num_payments - 1:
            principal_amount = outstanding_balance
        else:
            principal_amount = principal_per_payment

        principal_payment = Money(amount=principal_amount, currency=principal.currency)

        # Create cash flows
        cash_flows.append(
            CashFlow(
                date=payment_date,
                amount=interest,
                type=CashFlowType.INTEREST,
                description=f"Payment {i+1}/{num_payments} - Interest"
            )
        )

        cash_flows.append(
            CashFlow(
                date=payment_date,
                amount=principal_payment,
                type=CashFlowType.PRINCIPAL,
                description=f"Payment {i+1}/{num_payments} - Principal"
            )
        )

        # Update outstanding balance
        outstanding_balance -= principal_amount

    return CashFlowSchedule.from_list(cash_flows, sort=True)


def generate_interest_only_schedule(
    principal: Money,
    periodic_rate: Decimal,
    num_payments: int,
    payment_dates: list[date],
) -> CashFlowSchedule:
    """
    Generate interest-only schedule with balloon payment at maturity.

    Each payment is interest only on the full principal. At maturity, the full
    principal is due as a balloon payment.

    Args:
        principal: Initial loan principal
        periodic_rate: Interest rate per payment period
        num_payments: Total number of payments
        payment_dates: List of payment dates

    Returns:
        CashFlowSchedule with INTEREST and BALLOON flows

    Example:
        >>> principal = Money.from_float(200000)
        >>> rate = Decimal("0.004")
        >>> dates = [date(2024, i, 1) for i in range(1, 13)]
        >>> schedule = generate_interest_only_schedule(principal, rate, 12, dates)
    """
    if len(payment_dates) != num_payments:
        raise ValueError(
            f"Number of payment dates ({len(payment_dates)}) must match "
            f"number of payments ({num_payments})"
        )

    if num_payments == 0:
        raise ValueError("Interest-only loans must have at least one payment")

    cash_flows: list[CashFlow] = []

    # Interest payment is constant (on full principal)
    interest_amount = principal.amount * periodic_rate
    interest = Money(amount=interest_amount, currency=principal.currency)

    for i, payment_date in enumerate(payment_dates):
        # Interest payment
        cash_flows.append(
            CashFlow(
                date=payment_date,
                amount=interest,
                type=CashFlowType.INTEREST,
                description=f"Payment {i+1}/{num_payments} - Interest"
            )
        )

        # Balloon payment on last date
        if i == num_payments - 1:
            cash_flows.append(
                CashFlow(
                    date=payment_date,
                    amount=principal,
                    type=CashFlowType.BALLOON,
                    description="Balloon payment at maturity"
                )
            )

    return CashFlowSchedule.from_list(cash_flows, sort=True)


def generate_bullet_schedule(
    principal: Money,
    maturity_date: date,
) -> CashFlowSchedule:
    """
    Generate bullet payment schedule.

    Single payment of full principal at maturity. No periodic payments.

    Args:
        principal: Loan principal
        maturity_date: Date of bullet payment

    Returns:
        CashFlowSchedule with single BALLOON flow

    Example:
        >>> principal = Money.from_float(1000000)
        >>> schedule = generate_bullet_schedule(principal, date(2025, 12, 31))
    """
    cash_flow = CashFlow(
        date=maturity_date,
        amount=principal,
        type=CashFlowType.BALLOON,
        description="Bullet payment at maturity"
    )

    return CashFlowSchedule(cash_flows=(cash_flow,))
