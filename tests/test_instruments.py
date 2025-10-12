"""Tests for loan instruments and amortization."""

from datetime import date
from decimal import Decimal

import pytest

from credkit import InterestRate, Money, PaymentFrequency, Period
from credkit.cashflow import CashFlowType
from credkit.instruments import AmortizationType, Loan
from credkit.instruments.amortization import (
    calculate_level_payment,
    generate_bullet_schedule,
    generate_interest_only_schedule,
    generate_level_payment_schedule,
    generate_level_principal_schedule,
    generate_payment_dates,
)
from credkit.temporal import BusinessDayCalendar, BusinessDayConvention


class TestAmortizationType:
    """Tests for AmortizationType enum."""

    def test_enum_values(self):
        """Test enum has expected values."""
        assert AmortizationType.LEVEL_PAYMENT.value == "Level Payment"
        assert AmortizationType.LEVEL_PRINCIPAL.value == "Level Principal"
        assert AmortizationType.INTEREST_ONLY.value == "Interest Only"
        assert AmortizationType.BULLET.value == "Bullet"

    def test_string_representation(self):
        """Test string conversion."""
        assert str(AmortizationType.LEVEL_PAYMENT) == "Level Payment"


class TestCalculateLevelPayment:
    """Tests for level payment calculation."""

    def test_standard_mortgage(self):
        """Test typical 30-year mortgage payment."""
        principal = Money.from_float(300000.0)
        # 6.5% annual = 0.065/12 = 0.00541667 monthly
        periodic_rate = Decimal("0.065") / Decimal("12")
        num_payments = 360  # 30 years * 12 months

        payment = calculate_level_payment(principal, periodic_rate, num_payments)

        # Expected: approximately $1896.20
        assert payment.amount > Decimal("1895")
        assert payment.amount < Decimal("1897")

    def test_zero_interest(self):
        """Test loan with zero interest rate."""
        principal = Money.from_float(12000.0)
        periodic_rate = Decimal("0")
        num_payments = 12

        payment = calculate_level_payment(principal, periodic_rate, num_payments)

        # With 0% interest, payment = principal / num_payments
        assert payment == principal / num_payments
        assert payment.amount == Decimal("1000")

    def test_short_term_loan(self):
        """Test short-term personal loan."""
        principal = Money.from_float(5000.0)
        periodic_rate = Decimal("0.10") / Decimal("12")  # 10% APR
        num_payments = 12

        payment = calculate_level_payment(principal, periodic_rate, num_payments)

        # Payment should be slightly over principal/12 due to interest
        assert payment.amount > principal.amount / Decimal("12")

    def test_single_payment(self):
        """Test loan with single payment."""
        principal = Money.from_float(1000.0)
        periodic_rate = Decimal("0.05")
        num_payments = 1

        payment = calculate_level_payment(principal, periodic_rate, num_payments)

        # Single payment = principal * (1 + rate)
        expected = principal.amount * (Decimal("1") + periodic_rate)
        assert abs(payment.amount - expected) < Decimal("0.01")

    def test_negative_rate_raises_error(self):
        """Test that negative rate raises ValueError."""
        principal = Money.from_float(1000.0)
        periodic_rate = Decimal("-0.01")
        num_payments = 12

        with pytest.raises(ValueError, match="non-negative"):
            calculate_level_payment(principal, periodic_rate, num_payments)

    def test_zero_payments_raises_error(self):
        """Test that zero payments raises ValueError."""
        principal = Money.from_float(1000.0)
        periodic_rate = Decimal("0.05")
        num_payments = 0

        with pytest.raises(ValueError, match="must be positive"):
            calculate_level_payment(principal, periodic_rate, num_payments)


class TestGeneratePaymentDates:
    """Tests for payment date generation."""

    def test_monthly_payments(self):
        """Test monthly payment date generation."""
        start_date = date(2024, 1, 15)
        dates = generate_payment_dates(
            start_date,
            PaymentFrequency.MONTHLY,
            12,
        )

        assert len(dates) == 12
        assert dates[0] == date(2024, 1, 15)
        assert dates[1] == date(2024, 2, 15)
        assert dates[-1] == date(2024, 12, 15)  # 12 months from start

    def test_quarterly_payments(self):
        """Test quarterly payment date generation."""
        start_date = date(2024, 1, 1)
        dates = generate_payment_dates(
            start_date,
            PaymentFrequency.QUARTERLY,
            4,
        )

        assert len(dates) == 4
        assert dates[0] == date(2024, 1, 1)
        assert dates[1] == date(2024, 4, 1)
        assert dates[2] == date(2024, 7, 1)
        assert dates[3] == date(2024, 10, 1)

    def test_business_day_adjustment(self):
        """Test payment dates adjusted for business days."""
        # Start on a Saturday (2024-01-06)
        start_date = date(2024, 1, 6)
        calendar = BusinessDayCalendar(name="TEST")

        dates = generate_payment_dates(
            start_date,
            PaymentFrequency.MONTHLY,
            3,
            calendar=calendar,
            convention=BusinessDayConvention.FOLLOWING,
        )

        # Saturday should be adjusted to Monday
        assert dates[0] == date(2024, 1, 8)

    def test_zero_payments(self):
        """Test that zero payments returns empty list."""
        dates = generate_payment_dates(
            date(2024, 1, 1),
            PaymentFrequency.MONTHLY,
            0,
        )

        assert dates == []


class TestLevelPaymentSchedule:
    """Tests for level payment schedule generation."""

    def test_simple_level_payment_schedule(self):
        """Test generation of simple level payment schedule."""
        principal = Money.from_float(12000.0)
        periodic_rate = Decimal("0.01")  # 1% per month
        num_payments = 12
        payment_amount = Money.from_float(1065.0)  # Approximate
        payment_dates = [date(2024, i, 1) for i in range(1, 13)]

        schedule = generate_level_payment_schedule(
            principal, periodic_rate, num_payments, payment_dates, payment_amount
        )

        # Should have 24 cash flows (12 interest + 12 principal)
        assert len(schedule) == 24

        # Get principal and interest totals
        principal_total = schedule.get_principal_flows().total_amount()
        interest_total = schedule.get_interest_flows().total_amount()

        # Principal should equal original loan amount
        assert abs(principal_total.amount - principal.amount) < Decimal("0.01")

        # Interest should be positive
        assert interest_total.is_positive()

    def test_first_payment_breakdown(self):
        """Test interest/principal split in first payment."""
        principal = Money.from_float(100000.0)
        periodic_rate = Decimal("0.005")  # 0.5% per month
        num_payments = 360
        payment_amount = calculate_level_payment(principal, periodic_rate, num_payments)
        payment_dates = [date(2024, i, 1) for i in range(1, 13)]  # Generate 12 months

        schedule = generate_level_payment_schedule(
            principal, periodic_rate, 12, payment_dates, payment_amount
        )

        # Should have 24 flows (12 * 2 flows per payment)
        assert len(schedule) == 24

        # Test first payment's interest/principal split
        interest_flows = schedule.get_interest_flows()
        principal_flows = schedule.get_principal_flows()

        first_interest = interest_flows[0]
        first_principal = principal_flows[0]

        # First interest should be balance * rate
        expected_interest = principal.amount * periodic_rate
        assert abs(first_interest.amount.amount - expected_interest) < Decimal("0.01")

        # First principal should be payment - interest
        expected_principal = payment_amount.amount - expected_interest
        assert abs(first_principal.amount.amount - expected_principal) < Decimal("0.01")

    def test_mismatched_dates_raises_error(self):
        """Test that mismatched payment dates raises ValueError."""
        principal = Money.from_float(1000.0)
        periodic_rate = Decimal("0.01")
        num_payments = 12
        payment_amount = Money.from_float(100.0)
        payment_dates = [date(2024, 1, 1)]  # Only 1 date, but 12 payments

        with pytest.raises(ValueError, match="must match"):
            generate_level_payment_schedule(
                principal, periodic_rate, num_payments, payment_dates, payment_amount
            )


class TestLevelPrincipalSchedule:
    """Tests for level principal schedule generation."""

    def test_level_principal_schedule(self):
        """Test level principal schedule generation."""
        principal = Money.from_float(12000.0)
        periodic_rate = Decimal("0.01")
        num_payments = 12
        payment_dates = [date(2024, i, 1) for i in range(1, 13)]

        schedule = generate_level_principal_schedule(
            principal, periodic_rate, num_payments, payment_dates
        )

        # Should have 24 cash flows
        assert len(schedule) == 24

        # Principal total should equal original
        principal_total = schedule.get_principal_flows().total_amount()
        assert abs(principal_total.amount - principal.amount) < Decimal("0.01")

        # Each principal payment should be approximately equal
        principal_flows = schedule.get_principal_flows()
        expected_principal_per_payment = principal.amount / Decimal(num_payments)

        for flow in principal_flows:
            assert abs(flow.amount.amount - expected_principal_per_payment) < Decimal("0.01")


class TestInterestOnlySchedule:
    """Tests for interest-only schedule generation."""

    def test_interest_only_with_balloon(self):
        """Test interest-only schedule with balloon payment."""
        principal = Money.from_float(200000.0)
        periodic_rate = Decimal("0.004")  # 0.4% per month
        num_payments = 60
        payment_dates = [date(2024 + i // 12, (i % 12) + 1, 1) for i in range(60)]

        schedule = generate_interest_only_schedule(
            principal, periodic_rate, num_payments, payment_dates
        )

        # Should have 61 cash flows (60 interest + 1 balloon)
        assert len(schedule) == 61

        # Get interest and balloon separately
        interest_flows = schedule.filter_by_type(CashFlowType.INTEREST)
        balloon_flows = schedule.filter_by_type(CashFlowType.BALLOON)

        assert len(interest_flows) == 60
        assert len(balloon_flows) == 1

        # Each interest payment should be the same
        expected_interest = principal.amount * periodic_rate
        for flow in interest_flows:
            assert abs(flow.amount.amount - expected_interest) < Decimal("0.01")

        # Balloon should equal principal
        assert balloon_flows[0].amount == principal

    def test_interest_only_single_payment(self):
        """Test interest-only with single payment."""
        principal = Money.from_float(10000.0)
        periodic_rate = Decimal("0.005")
        num_payments = 1
        payment_dates = [date(2024, 12, 31)]

        schedule = generate_interest_only_schedule(
            principal, periodic_rate, num_payments, payment_dates
        )

        # Should have 2 flows (interest + balloon)
        assert len(schedule) == 2

    def test_interest_only_zero_payments_raises_error(self):
        """Test that zero payments raises ValueError."""
        principal = Money.from_float(10000.0)
        periodic_rate = Decimal("0.005")
        num_payments = 0
        payment_dates = []

        with pytest.raises(ValueError, match="at least one payment"):
            generate_interest_only_schedule(
                principal, periodic_rate, num_payments, payment_dates
            )


class TestBulletSchedule:
    """Tests for bullet schedule generation."""

    def test_bullet_schedule(self):
        """Test bullet payment schedule."""
        principal = Money.from_float(1000000.0)
        maturity_date = date(2029, 12, 31)

        schedule = generate_bullet_schedule(principal, maturity_date)

        # Should have single flow
        assert len(schedule) == 1

        # Should be a balloon payment
        flow = schedule[0]
        assert flow.type == CashFlowType.BALLOON
        assert flow.amount == principal
        assert flow.date == maturity_date


class TestLoanCreation:
    """Tests for Loan class creation and validation."""

    def test_create_basic_loan(self):
        """Test creating a basic loan."""
        loan = Loan(
            principal=Money.from_float(100000.0),
            annual_rate=InterestRate.from_percent(6.0),
            term=Period.from_string("30Y"),
            payment_frequency=PaymentFrequency.MONTHLY,
            amortization_type=AmortizationType.LEVEL_PAYMENT,
            origination_date=date(2024, 1, 1),
        )

        assert loan.principal.amount == Decimal("100000.0")
        assert loan.annual_rate.to_percent() == Decimal("6.0")
        assert loan.term == Period.from_string("30Y")

    def test_from_float_factory(self):
        """Test creating loan from float values."""
        loan = Loan.from_float(
            principal=50000.0,
            annual_rate_percent=5.5,
            term_years=15,
            origination_date=date(2024, 1, 1),
        )

        assert loan.principal.amount == Decimal("50000.0")
        assert loan.annual_rate.to_percent() == Decimal("5.5")

    def test_mortgage_factory(self):
        """Test mortgage factory method."""
        loan = Loan.mortgage(
            principal=Money.from_float(400000.0),
            annual_rate=InterestRate.from_percent(6.875),
            term_years=30,
            origination_date=date(2024, 1, 1),
        )

        assert loan.amortization_type == AmortizationType.LEVEL_PAYMENT
        assert loan.payment_frequency == PaymentFrequency.MONTHLY
        assert loan.term == Period.from_string("30Y")

    def test_auto_loan_factory(self):
        """Test auto loan factory method."""
        loan = Loan.auto_loan(
            principal=Money.from_float(35000.0),
            annual_rate=InterestRate.from_percent(5.5),
            term_months=72,
            origination_date=date(2024, 1, 1),
        )

        assert loan.amortization_type == AmortizationType.LEVEL_PAYMENT
        assert loan.payment_frequency == PaymentFrequency.MONTHLY
        assert loan.term == Period.from_string("72M")

    def test_personal_loan_factory(self):
        """Test personal loan factory method."""
        loan = Loan.personal_loan(
            principal=Money.from_float(10000.0),
            annual_rate=InterestRate.from_percent(12.0),
            term_months=48,
            origination_date=date(2024, 1, 1),
        )

        assert loan.amortization_type == AmortizationType.LEVEL_PAYMENT
        assert loan.payment_frequency == PaymentFrequency.MONTHLY

    def test_negative_principal_raises_error(self):
        """Test that negative principal raises ValueError."""
        with pytest.raises(ValueError, match="must be positive"):
            Loan(
                principal=Money.from_float(-1000.0),
                annual_rate=InterestRate.from_percent(6.0),
                term=Period.from_string("5Y"),
                payment_frequency=PaymentFrequency.MONTHLY,
                amortization_type=AmortizationType.LEVEL_PAYMENT,
                origination_date=date(2024, 1, 1),
            )

    def test_zero_principal_raises_error(self):
        """Test that zero principal raises ValueError."""
        with pytest.raises(ValueError, match="must be positive"):
            Loan(
                principal=Money.zero(),
                annual_rate=InterestRate.from_percent(6.0),
                term=Period.from_string("5Y"),
                payment_frequency=PaymentFrequency.MONTHLY,
                amortization_type=AmortizationType.LEVEL_PAYMENT,
                origination_date=date(2024, 1, 1),
            )

    def test_negative_rate_raises_error(self):
        """Test that negative rate raises ValueError."""
        with pytest.raises(ValueError, match="non-negative"):
            Loan(
                principal=Money.from_float(100000.0),
                annual_rate=InterestRate(rate=Decimal("-0.01")),
                term=Period.from_string("5Y"),
                payment_frequency=PaymentFrequency.MONTHLY,
                amortization_type=AmortizationType.LEVEL_PAYMENT,
                origination_date=date(2024, 1, 1),
            )

    def test_zero_coupon_frequency_with_amortization_raises_error(self):
        """Test that ZERO_COUPON frequency with non-bullet amortization raises error."""
        with pytest.raises(ValueError, match="ZERO_COUPON"):
            Loan(
                principal=Money.from_float(100000.0),
                annual_rate=InterestRate.from_percent(6.0),
                term=Period.from_string("5Y"),
                payment_frequency=PaymentFrequency.ZERO_COUPON,
                amortization_type=AmortizationType.LEVEL_PAYMENT,
                origination_date=date(2024, 1, 1),
            )

    def test_first_payment_before_origination_raises_error(self):
        """Test that first payment before origination raises error."""
        with pytest.raises(ValueError, match="must be after"):
            Loan(
                principal=Money.from_float(100000.0),
                annual_rate=InterestRate.from_percent(6.0),
                term=Period.from_string("5Y"),
                payment_frequency=PaymentFrequency.MONTHLY,
                amortization_type=AmortizationType.LEVEL_PAYMENT,
                origination_date=date(2024, 1, 1),
                first_payment_date=date(2023, 12, 31),
            )


class TestLoanCalculations:
    """Tests for loan calculation methods."""

    def test_calculate_periodic_rate(self):
        """Test periodic rate calculation."""
        loan = Loan.mortgage(
            principal=Money.from_float(100000.0),
            annual_rate=InterestRate.from_percent(6.0),
            origination_date=date(2024, 1, 1),
        )

        periodic_rate = loan.calculate_periodic_rate()

        # 6% annual / 12 months = 0.5% monthly
        expected = Decimal("0.06") / Decimal("12")
        assert periodic_rate == expected

    def test_calculate_number_of_payments(self):
        """Test number of payments calculation."""
        loan = Loan.mortgage(
            principal=Money.from_float(200000.0),
            annual_rate=InterestRate.from_percent(5.0),
            term_years=30,
            origination_date=date(2024, 1, 1),
        )

        num_payments = loan.calculate_number_of_payments()

        # 30 years * 12 months = 360 payments
        assert num_payments == 360

    def test_calculate_payment_level_payment(self):
        """Test payment calculation for level payment loan."""
        loan = Loan.from_float(
            principal=100000.0,
            annual_rate_percent=6.0,
            term_years=30,
            origination_date=date(2024, 1, 1),
        )

        payment = loan.calculate_payment()

        # Expected: approximately $599.55
        assert payment.amount > Decimal("599")
        assert payment.amount < Decimal("600")

    def test_calculate_maturity_date(self):
        """Test maturity date calculation."""
        loan = Loan.from_float(
            principal=100000.0,
            annual_rate_percent=6.0,
            term_years=5,
            origination_date=date(2024, 1, 15),
        )

        maturity = loan.maturity_date()

        # First payment is 2024-02-15, 60 payments later is 2029-01-15
        assert maturity.year == 2029
        assert maturity.month == 1
        assert maturity.day == 15

    def test_bullet_maturity_date(self):
        """Test maturity date for bullet loan."""
        loan = Loan(
            principal=Money.from_float(100000.0),
            annual_rate=InterestRate.from_percent(5.0),
            term=Period.from_string("3Y"),
            payment_frequency=PaymentFrequency.MONTHLY,
            amortization_type=AmortizationType.BULLET,
            origination_date=date(2024, 1, 1),
        )

        maturity = loan.maturity_date()

        # Should be 3 years from origination
        assert maturity == date(2027, 1, 1)


class TestLoanScheduleGeneration:
    """Tests for loan schedule generation."""

    def test_generate_level_payment_schedule(self):
        """Test generating level payment schedule."""
        loan = Loan.from_float(
            principal=120000.0,
            annual_rate_percent=6.0,
            term_years=30,
            origination_date=date(2024, 1, 1),
        )

        schedule = loan.generate_schedule()

        # Should have 720 cash flows (360 payments * 2 flows per payment)
        assert len(schedule) == 720

        # Principal total should equal original loan
        principal_total = schedule.get_principal_flows().total_amount()
        assert abs(principal_total.amount - Decimal("120000")) < Decimal("1.0")

        # Interest should be positive
        interest_total = schedule.get_interest_flows().total_amount()
        assert interest_total.is_positive()

    def test_generate_interest_only_schedule(self):
        """Test generating interest-only schedule."""
        loan = Loan(
            principal=Money.from_float(100000.0),
            annual_rate=InterestRate.from_percent(5.0),
            term=Period.from_string("5Y"),
            payment_frequency=PaymentFrequency.MONTHLY,
            amortization_type=AmortizationType.INTEREST_ONLY,
            origination_date=date(2024, 1, 1),
        )

        schedule = loan.generate_schedule()

        # Should have 61 flows (60 interest + 1 balloon)
        assert len(schedule) == 61

        balloon_flows = schedule.filter_by_type(CashFlowType.BALLOON)
        assert len(balloon_flows) == 1
        assert balloon_flows[0].amount == loan.principal

    def test_generate_bullet_schedule(self):
        """Test generating bullet schedule."""
        loan = Loan(
            principal=Money.from_float(500000.0),
            annual_rate=InterestRate.from_percent(4.0),
            term=Period.from_string("10Y"),
            payment_frequency=PaymentFrequency.MONTHLY,
            amortization_type=AmortizationType.BULLET,
            origination_date=date(2024, 1, 1),
        )

        schedule = loan.generate_schedule()

        # Should have single flow
        assert len(schedule) == 1
        assert schedule[0].type == CashFlowType.BALLOON
        assert schedule[0].amount == loan.principal

    def test_total_interest_calculation(self):
        """Test total interest calculation."""
        loan = Loan.from_float(
            principal=100000.0,
            annual_rate_percent=5.0,
            term_years=15,
            origination_date=date(2024, 1, 1),
        )

        total_interest = loan.total_interest()

        # Should be positive and less than principal
        # (for reasonable rates and terms)
        assert total_interest.is_positive()
        assert total_interest.amount < loan.principal.amount

    def test_total_payments_calculation(self):
        """Test total payments calculation."""
        loan = Loan.from_float(
            principal=100000.0,
            annual_rate_percent=5.0,
            term_years=15,
            origination_date=date(2024, 1, 1),
        )

        total_payments = loan.total_payments()
        total_interest = loan.total_interest()

        # Total payments should equal principal + interest
        expected = loan.principal + total_interest
        assert abs(total_payments.amount - expected.amount) < Decimal("1.0")


class TestLoanEdgeCases:
    """Tests for edge cases and special scenarios."""

    def test_zero_interest_loan(self):
        """Test loan with 0% interest."""
        loan = Loan(
            principal=Money.from_float(12000.0),
            annual_rate=InterestRate.from_percent(0.0),
            term=Period.from_string("1Y"),
            payment_frequency=PaymentFrequency.MONTHLY,
            amortization_type=AmortizationType.LEVEL_PAYMENT,
            origination_date=date(2024, 1, 1),
        )

        payment = loan.calculate_payment()

        # With 0% interest, payment = principal / num_payments
        assert payment == loan.principal / 12

        schedule = loan.generate_schedule()
        interest_total = schedule.get_interest_flows().total_amount()

        # Total interest should be zero
        assert interest_total.is_zero()

    def test_single_payment_loan(self):
        """Test loan with single payment."""
        loan = Loan(
            principal=Money.from_float(1000.0),
            annual_rate=InterestRate.from_percent(5.0),
            term=Period.from_string("1M"),
            payment_frequency=PaymentFrequency.MONTHLY,
            amortization_type=AmortizationType.LEVEL_PAYMENT,
            origination_date=date(2024, 1, 1),
        )

        schedule = loan.generate_schedule()

        # Should have 2 flows (interest + principal)
        assert len(schedule) == 2

        principal_total = schedule.get_principal_flows().total_amount()
        assert abs(principal_total.amount - loan.principal.amount) < Decimal("0.01")

    def test_custom_first_payment_date(self):
        """Test loan with custom first payment date."""
        loan = Loan(
            principal=Money.from_float(100000.0),
            annual_rate=InterestRate.from_percent(6.0),
            term=Period.from_string("5Y"),
            payment_frequency=PaymentFrequency.MONTHLY,
            amortization_type=AmortizationType.LEVEL_PAYMENT,
            origination_date=date(2024, 1, 1),
            first_payment_date=date(2024, 3, 1),  # 2 months after origination
        )

        schedule = loan.generate_schedule()

        # First payment should be on specified date
        assert schedule.earliest_date() == date(2024, 3, 1)

    def test_loan_string_representation(self):
        """Test string representation of loan."""
        loan = Loan.from_float(
            principal=100000.0,
            annual_rate_percent=6.0,
            term_years=30,
            origination_date=date(2024, 1, 1),
        )

        loan_str = str(loan)
        assert "100,000" in loan_str  # Money formats with commas
        assert "6.00" in loan_str
        assert "30Y" in loan_str
