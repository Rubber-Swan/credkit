"""
credkit: An open credit modeling toolkit.

Elegant Python tools for credit risk modeling, starting with domain-driven
primitive data types for cash flow modeling and credit risk analytics.

Core modules:
- temporal: Date, period, and day count primitives
- money: Currency, monetary amounts, and interest rates
- cashflow: Cash flow modeling and present value calculations
- instruments: Loan instruments and amortization schedules
"""

from .cashflow import (
    CashFlow,
    CashFlowSchedule,
    CashFlowType,
    DiscountCurve,
    FlatDiscountCurve,
    InterpolationType,
    ZeroCurve,
)
from .money import (
    Currency,
    Money,
    InterestRate,
    CompoundingConvention,
    Spread,
    USD,
)
from .temporal import (
    DayCountConvention,
    DayCountBasis,
    Period,
    PaymentFrequency,
    BusinessDayCalendar,
    BusinessDayConvention,
)
from .instruments import (
    AmortizationType,
    Loan,
)

__version__ = "0.2.0"

__all__ = [
    # Money module
    "Currency",
    "Money",
    "InterestRate",
    "CompoundingConvention",
    "Spread",
    "USD",
    # Temporal module
    "DayCountConvention",
    "DayCountBasis",
    "Period",
    "PaymentFrequency",
    "BusinessDayCalendar",
    "BusinessDayConvention",
    # Cash flow module
    "CashFlow",
    "CashFlowSchedule",
    "CashFlowType",
    "DiscountCurve",
    "FlatDiscountCurve",
    "ZeroCurve",
    "InterpolationType",
    # Instruments module
    "AmortizationType",
    "Loan",
]
