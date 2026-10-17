"""Pure per-expense reimbursement limits (RN-001, RN-002 and RN-004)."""

from collections.abc import Set
from dataclasses import dataclass
from datetime import date
from decimal import Decimal, localcontext

from reembolso.category_rules import normalize_category
from reembolso.models import Expense, Policy, Reason


@dataclass(frozen=True)
class LimitEvaluation:
    """Outcome of applying the normal or travel limit to one expense."""

    status: str
    reimbursable_value: Decimal
    reasons: tuple[Reason, ...]
    applied_limit: Decimal | None = None

    @property
    def terminal(self) -> bool:
        return self.status in {"recusada", "revisao_manual"}


def _increase_limit(limit: Decimal, percent: Decimal) -> Decimal:
    """Increase a limit without rounding it to presentation precision."""

    required_precision = (
        len(limit.as_tuple().digits)
        + len(percent.as_tuple().digits)
        + abs(limit.as_tuple().exponent)
        + abs(percent.as_tuple().exponent)
        + 4
    )
    with localcontext() as context:
        context.prec = max(context.prec, required_precision)
        return limit + (limit * percent / Decimal("100"))


def apply_expense_limit(
    expense: Expense,
    reported_value: Decimal | None,
    policy: Policy,
    cost_center: str,
    travel_days: Set[date],
    current_status: str | None = None,
    current_reasons: tuple[Reason, ...] = (),
) -> LimitEvaluation:
    """Apply step 9 to one expense, preserving terminal earlier outcomes.

    Category membership, zero limits, missing exchange rates and manual review
    are handled by earlier steps. Invalid non-terminal inputs therefore signal
    an orchestration error rather than silently inventing another decision.
    """

    if current_status in {"recusada", "revisao_manual"}:
        return LimitEvaluation(
            status=current_status,
            reimbursable_value=Decimal("0"),
            reasons=current_reasons,
        )
    if current_status is not None:
        raise ValueError("status anterior nao terminal inesperado no passo de limite")
    if reported_value is None:
        raise ValueError("valor informado ausente em despesa elegivel")

    category = expense.normalized_category or normalize_category(expense.category)
    rule = policy.rule_for(cost_center, category)
    if rule is None:
        raise ValueError("regra de categoria ausente em despesa elegivel")
    if rule.limit == Decimal("0"):
        raise ValueError("limite zero deveria ter sido tratado antes do passo 9")

    is_travel_day = expense.date in travel_days
    limit = (
        _increase_limit(rule.limit, policy.travel_increase_percent)
        if is_travel_day
        else rule.limit
    )
    reasons = list(current_reasons)
    if is_travel_day:
        reasons.append(
            Reason(
                code="limite_viagem_aplicado",
                description="Limite ampliado de viagem aplicado a esta despesa.",
            )
        )

    if reported_value <= limit:
        reasons.append(
            Reason(
                code="dentro_do_limite",
                description="Valor integral aprovado por estar dentro do limite.",
            )
        )
        return LimitEvaluation(
            status="reembolsada",
            reimbursable_value=reported_value,
            reasons=tuple(reasons),
            applied_limit=limit,
        )

    reasons.append(
        Reason(
            code="limite_aplicado",
            description="Valor reembolsavel reduzido ao limite da politica.",
        )
    )
    return LimitEvaluation(
        status="reembolsada_parcialmente",
        reimbursable_value=limit,
        reasons=tuple(reasons),
        applied_limit=limit,
    )
