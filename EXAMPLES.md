# credkit Examples

Comprehensive examples for all credkit modules and features.

## Table of Contents

- [Temporal Module](#temporal-module)
- [Money Module](#money-module)
- [Cash Flow Module](#cash-flow-module)
- [Loan Instruments](#loan-instruments)

## Temporal Module

Time and date primitives for financial calculations.

### Day Count Conventions

Industry-standard conventions for interest accrual:

```python
from credkit.temporal import DayCountBasis, DayCountConvention
from datetime import date

basis = DayCountBasis(DayCountConvention.ACTUAL_365)
year_fraction = basis.year_fraction(date(2024, 1, 1), date(2024, 7, 1))
```

Supports ACT/365, ACT/360, ACT/ACT, 30/360 (US), 30E/360, and more.

### Periods

Time spans with natural syntax:

```python
from credkit.temporal import Period

term = Period.from_string("5Y")   # 5 years
grace = Period.from_string("90D")  # 90 days

# Add to dates
import datetime
maturity = term.add_to_date(datetime.date(2024, 1, 1))
```

### Payment Frequencies

Standard schedules:

```python
from credkit.temporal import PaymentFrequency

freq = PaymentFrequency.MONTHLY
print(freq.payments_per_year)  # 12
print(freq.period)  # Period(1M)
```

### Business Day Calendars

Holiday-aware date adjustments:

```python
from credkit.temporal import BusinessDayCalendar, BusinessDayConvention

calendar = BusinessDayCalendar(name="US")
adjusted = calendar.adjust(some_date, BusinessDayConvention.FOLLOWING)
biz_days = calendar.business_days_between(start, end)
```

## Money Module

Financial primitives with Decimal precision.

### Money

Currency-aware monetary amounts:

```python
from credkit import Money, USD
from decimal import Decimal

principal = Money(Decimal("100000.00"), USD)
interest = Money.from_float(542.50)

total = principal + interest
monthly = total / 12

print(total)  # "USD 100,542.50"
```

All arithmetic operations preserve precision and prevent mixing currencies.

### Interest Rates

APR with multiple compounding conventions:

```python
from credkit import InterestRate, CompoundingConvention
from decimal import Decimal

# 5.25% APR with monthly compounding (default for consumer loans)
rate = InterestRate.from_percent(5.25)

# Calculate present value discount factor
pv_factor = rate.discount_factor(Decimal("10"))  # 10 years

# Convert between compounding conventions
annual_equiv = rate.convert_to(CompoundingConvention.ANNUAL)
```

Supports simple, annual, quarterly, monthly, daily, and continuous compounding.

### Spreads

Basis point adjustments:

```python
from credkit import Spread

# Prime + 250 basis points
spread = Spread.from_bps(250)
prime_rate = InterestRate.from_percent(8.5)

loan_rate = spread.apply_to(prime_rate)  # 10.75%
```

## Cash Flow Module

Present value calculations and payment schedules.

### Cash Flows

Individual payment representation:

```python
from credkit import CashFlow, CashFlowType, Money
from datetime import date

# Create individual cash flows
principal_payment = CashFlow(
    date=date(2025, 1, 1),
    amount=Money.from_float(1000.0),
    type=CashFlowType.PRINCIPAL,
    description="Monthly principal payment"
)

interest_payment = CashFlow(
    date=date(2025, 1, 1),
    amount=Money.from_float(250.0),
    type=CashFlowType.INTEREST
)
```

### Discount Curves

Present value calculations:

```python
from credkit import FlatDiscountCurve, InterestRate
from datetime import date

# Simple flat curve using one rate
rate = InterestRate.from_percent(6.5)
curve = FlatDiscountCurve(rate, valuation_date=date(2024, 1, 1))

# Calculate present value of future cash flow
pv = principal_payment.present_value(curve)

# Or use sophisticated zero curve with multiple points
from credkit import ZeroCurve

curve = ZeroCurve.from_rates(
    valuation_date=date(2024, 1, 1),
    rates=[
        (date(2025, 1, 1), 0.050),  # 5.0% at 1 year
        (date(2026, 1, 1), 0.055),  # 5.5% at 2 years
        (date(2027, 1, 1), 0.060),  # 6.0% at 3 years
    ]
)

# Get spot and forward rates
spot = curve.spot_rate(date(2025, 6, 1))
forward = curve.forward_rate(date(2025, 1, 1), date(2026, 1, 1))
```

### Cash Flow Schedules

Collections with NPV:

```python
from credkit import CashFlowSchedule

# Create schedule from list of cash flows
schedule = CashFlowSchedule.from_list([
    principal_payment,
    interest_payment,
    # ... more flows
])

# Filter and aggregate
principal_only = schedule.get_principal_flows()
by_type = schedule.sum_by_type()

# Calculate NPV
npv = schedule.present_value(curve)
print(f"Net Present Value: {npv}")

# Aggregate daily flows into monthly buckets
from credkit import PaymentFrequency
monthly = schedule.aggregate_by_period(PaymentFrequency.MONTHLY)
```

## Loan Instruments

End-to-end consumer loan modeling.

### Loan Creation

Multiple ways to create loans:

```python
from credkit import Loan, Money, InterestRate, Period, PaymentFrequency, AmortizationType
from datetime import date

# Method 1: Direct construction
loan = Loan(
    principal=Money.from_float(300000.0),
    annual_rate=InterestRate.from_percent(6.5),
    term=Period.from_string("30Y"),
    payment_frequency=PaymentFrequency.MONTHLY,
    amortization_type=AmortizationType.LEVEL_PAYMENT,
    origination_date=date(2024, 1, 1),
)

# Method 2: Quick creation from floats
loan = Loan.from_float(
    principal=300000.0,
    annual_rate_percent=6.5,
    term_years=30,
    origination_date=date(2024, 1, 1),
)

# Method 3: Use factory methods for common loan types
loan = Loan.mortgage(
    principal=Money.from_float(400000.0),
    annual_rate=InterestRate.from_percent(6.875),
    term_years=30,
)

auto_loan = Loan.auto_loan(
    principal=Money.from_float(35000.0),
    annual_rate=InterestRate.from_percent(5.5),
    term_months=72,
)

personal_loan = Loan.personal_loan(
    principal=Money.from_float(10000.0),
    annual_rate=InterestRate.from_percent(12.0),
    term_months=48,
)
```

### Payment Calculations

Calculate loan payments and totals:

```python
# Calculate monthly payment
payment = loan.calculate_payment()
print(f"Monthly payment: {payment}")  # $1,896.20

# Get loan details
maturity = loan.maturity_date()
total_interest = loan.total_interest()
total_payments = loan.total_payments()

print(f"Total interest over life of loan: {total_interest}")
print(f"Total amount paid: {total_payments}")
```

### Amortization Schedules

Generate complete payment schedules:

```python
# Generate full amortization schedule as CashFlowSchedule
schedule = loan.generate_schedule()

# Schedule contains all payments broken down by type
print(f"Total payments: {len(schedule)}")  # 720 (360 principal + 360 interest)

# Analyze principal vs interest
principal_flows = schedule.get_principal_flows()
interest_flows = schedule.get_interest_flows()

print(f"Total principal: {principal_flows.total_amount()}")
print(f"Total interest: {interest_flows.total_amount()}")

# Filter payments by date range (e.g., first year)
first_year = schedule.filter_by_date_range(
    date(2024, 2, 1),
    date(2025, 1, 1),
)

year_1_interest = first_year.get_interest_flows().total_amount()
year_1_principal = first_year.get_principal_flows().total_amount()
```

### Amortization Types

Different payment structures:

```python
from credkit import AmortizationType

# Level payment (standard mortgages)
mortgage = Loan(
    principal=Money.from_float(200000.0),
    annual_rate=InterestRate.from_percent(6.0),
    term=Period.from_string("15Y"),
    payment_frequency=PaymentFrequency.MONTHLY,
    amortization_type=AmortizationType.LEVEL_PAYMENT,
    origination_date=date(2024, 1, 1),
)

# Interest-only with balloon
interest_only = Loan(
    principal=Money.from_float(500000.0),
    annual_rate=InterestRate.from_percent(5.5),
    term=Period.from_string("10Y"),
    payment_frequency=PaymentFrequency.MONTHLY,
    amortization_type=AmortizationType.INTEREST_ONLY,
    origination_date=date(2024, 1, 1),
)

# Bullet payment (single payment at maturity)
bullet = Loan(
    principal=Money.from_float(1000000.0),
    annual_rate=InterestRate.from_percent(4.0),
    term=Period.from_string("5Y"),
    payment_frequency=PaymentFrequency.MONTHLY,
    amortization_type=AmortizationType.BULLET,
    origination_date=date(2024, 1, 1),
)
```

### Integration with Valuation

Calculate loan present value:

```python
from credkit import FlatDiscountCurve

# Generate loan schedule
loan = Loan.mortgage(
    principal=Money.from_float(300000.0),
    annual_rate=InterestRate.from_percent(6.5),
    term_years=30,
    origination_date=date(2024, 1, 1),
)
schedule = loan.generate_schedule()

# Value loan using market discount rate
market_rate = InterestRate.from_percent(5.5)
curve = FlatDiscountCurve(market_rate, valuation_date=date(2024, 1, 1))

# Calculate present value
loan_value = schedule.present_value(curve)
print(f"Loan NPV at market rate: {loan_value}")

# Analyze interest rate sensitivity
for rate_pct in [5.0, 5.5, 6.0, 6.5, 7.0]:
    curve = FlatDiscountCurve(
        InterestRate.from_percent(rate_pct),
        valuation_date=date(2024, 1, 1)
    )
    pv = schedule.present_value(curve)
    print(f"PV at {rate_pct}%: {pv}")
```

## Complete End-to-End Example

Create a loan, generate schedule, and calculate NPV:

```python
from credkit import Loan, Money, InterestRate, FlatDiscountCurve
from datetime import date

# Create a 30-year mortgage
loan = Loan.mortgage(
    principal=Money.from_float(300000.0),
    annual_rate=InterestRate.from_percent(6.5),
    term_years=30,
    origination_date=date(2024, 1, 1),
)

# Calculate payment
payment = loan.calculate_payment()
print(f"Monthly payment: {payment}")

# Generate amortization schedule
schedule = loan.generate_schedule()
print(f"Total cash flows: {len(schedule)}")

# Calculate total interest
total_interest = loan.total_interest()
print(f"Total interest: {total_interest}")

# Value the loan at market rate
market_curve = FlatDiscountCurve(
    InterestRate.from_percent(5.5),
    valuation_date=date(2024, 1, 1)
)
npv = schedule.present_value(market_curve)
print(f"Market value: {npv}")

# Analyze first year payments
first_year = schedule.filter_by_date_range(date(2024, 2, 1), date(2025, 1, 1))
year_1_principal = first_year.get_principal_flows().total_amount()
year_1_interest = first_year.get_interest_flows().total_amount()
print(f"First year principal: {year_1_principal}")
print(f"First year interest: {year_1_interest}")
```
