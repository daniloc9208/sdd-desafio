"""Batch pre-analysis for travel days (RN-004, step 2)."""

from collections.abc import Iterable
from datetime import date, timedelta

from reembolso.category_rules import normalize_category
from reembolso.models import Expense


def identify_travel_days(expenses: Iterable[Expense]) -> frozenset[date]:
    """Return the calendar day after every positive lodging expense."""

    return frozenset(
        expense.date + timedelta(days=1)
        for expense in expenses
        if normalize_category(expense.category) == "hospedagem"
        and expense.original_value > 0
    )
