"""Monetary rounding and batch totals (RN-009, step 10)."""

from decimal import ROUND_HALF_UP, Decimal


def round_brl(value: Decimal) -> Decimal:
    """Round an unrounded BRL value to two decimal places (ROUND_HALF_UP).

    This is the ONLY place in the code where monetary rounding happens.
    The serializer (T-004) formats already-rounded values as strings; it does
    not round on its own.
    """
    return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
