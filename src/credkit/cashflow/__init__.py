"""
Cash flow module for modeling loan payment streams.

Provides primitives for individual cash flows, collections of cash flows,
and discount curves for present value calculations.
"""

from .cashflow import CashFlow, CashFlowType
from .discount import DiscountCurve, FlatDiscountCurve, InterpolationType, ZeroCurve
from .schedule import CashFlowSchedule

__all__ = [
    # Cash flow types
    "CashFlow",
    "CashFlowType",
    # Schedules
    "CashFlowSchedule",
    # Discount curves
    "DiscountCurve",
    "FlatDiscountCurve",
    "ZeroCurve",
    "InterpolationType",
]
