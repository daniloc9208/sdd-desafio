"""Pure monetary conversion used by the reimbursement calculation core."""

from dataclasses import dataclass
from decimal import Decimal, localcontext

from reembolso.models import ExchangeRates, Expense, Reason


@dataclass(frozen=True)
class CurrencyConversion:
    """BRL equivalent plus the source values required by the output contract."""

    reported_value: Decimal | None
    original_value: Decimal
    original_currency: str
    status: str | None = None
    reasons: tuple[Reason, ...] = ()

    @property
    def rejected(self) -> bool:
        """Whether conversion itself prevents reimbursement."""

        return self.status == "recusada"


def _multiply_exact(value: Decimal, rate: Decimal) -> Decimal:
    """Multiply finite decimals without rounding to the ambient context."""

    required_precision = len(value.as_tuple().digits) + len(rate.as_tuple().digits)
    with localcontext() as context:
        context.prec = max(context.prec, required_precision)
        return value * rate


def convert_expense_to_brl(
    expense: Expense,
    exchange_rates: ExchangeRates,
) -> CurrencyConversion:
    """Convert an expense with the eligible historical rate, without rounding."""

    rate = exchange_rates.rate_for(expense.original_currency, expense.date)
    if rate is None:
        return CurrencyConversion(
            reported_value=None,
            original_value=expense.original_value,
            original_currency=expense.original_currency,
            status="recusada",
            reasons=(
                Reason(
                    code="cotacao_indisponivel",
                    description=(
                        "Cotação indisponível para a moeda na data da despesa."
                    ),
                ),
            ),
        )

    return CurrencyConversion(
        reported_value=_multiply_exact(expense.original_value, rate),
        original_value=expense.original_value,
        original_currency=expense.original_currency,
    )
