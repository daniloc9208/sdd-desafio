"""Pure expense deadline validation according to RN-005."""

from dataclasses import dataclass
from datetime import date

from reembolso.models import Expense, Reason


@dataclass(frozen=True)
class DeadlineValidation:
    """Outcome of RN-005, suitable for short-circuiting item evaluation."""

    status: str | None = None
    reasons: tuple[Reason, ...] = ()

    @property
    def rejected(self) -> bool:
        """Whether the deadline rule rejects the current expense."""

        return self.status == "recusada"

    @property
    def terminal(self) -> bool:
        """Whether subsequent rules must be skipped for the current expense."""

        return self.rejected


def _rejection(code: str, description: str) -> DeadlineValidation:
    return DeadlineValidation(
        status="recusada",
        reasons=(Reason(code=code, description=description),),
    )


def validate_expense_deadline(
    expense: Expense,
    calculation_date: date,
) -> DeadlineValidation:
    """Apply only RN-005 to one expense using the injected calculation date."""

    elapsed_days = (calculation_date - expense.date).days
    if elapsed_days < 0:
        return _rejection(
            "data_futura",
            "A data da despesa é posterior à data do cálculo.",
        )
    if elapsed_days > 90:
        return _rejection(
            "prazo_excedido",
            "A despesa excede o prazo de apresentação de 90 dias corridos.",
        )
    return DeadlineValidation()
