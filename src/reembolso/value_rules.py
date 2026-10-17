"""Pure validation of expense values according to RN-008."""

from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal, localcontext

from reembolso.models import Expense, Reason


@dataclass(frozen=True)
class ValueValidation:
    """Outcome of RN-008, suitable for short-circuiting item evaluation."""

    status: str | None = None
    reasons: tuple[Reason, ...] = ()

    @property
    def rejected(self) -> bool:
        """Whether this rule rejects the current expense."""

        return self.status == "recusada"

    @property
    def terminal(self) -> bool:
        """Whether subsequent rules must be skipped for the current expense."""

        return self.rejected


def _round_brl(value: Decimal) -> Decimal:
    """Round BRL only for the RN-008 sub-cent test, without leaking rounding."""

    digits = len(value.as_tuple().digits)
    with localcontext() as context:
        context.prec = max(context.prec, digits + abs(value.as_tuple().exponent) + 2)
        return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def _rejection(code: str, description: str) -> ValueValidation:
    return ValueValidation(
        status="recusada",
        reasons=(Reason(code=code, description=description),),
    )


def validate_expense_value(
    expense: Expense,
    reported_value: Decimal | None,
) -> ValueValidation:
    """Apply only RN-008 to one expense.

    ``reported_value`` is the unrounded BRL equivalent produced by conversion.
    A missing equivalent is handled by the conversion rule, not by RN-008.
    """

    if expense.original_value == 0:
        return _rejection(
            "valor_zero_invalido",
            "Valor zero não é válido para reembolso.",
        )
    if expense.original_value < 0:
        return _rejection(
            "valor_negativo_fora_escopo",
            "Valor negativo pertence ao fluxo de estornos.",
        )
    if reported_value is not None and _round_brl(reported_value) == 0:
        return _rejection(
            "valor_inferior_ao_centavo",
            "Valor convertido é inferior a um centavo reembolsável.",
        )
    return ValueValidation()
