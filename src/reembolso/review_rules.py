"""Manual-review and zero-limit decisions (RN-004 and RN-012)."""

from collections.abc import Set
from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from reembolso.category_rules import normalize_category
from reembolso.models import CategoryRule, Expense, Reason


@dataclass(frozen=True)
class ReviewEvaluation:
    """Outcome of the zero-limit and manual-review steps for one item."""

    status: str | None = None
    reasons: tuple[Reason, ...] = ()

    @property
    def terminal(self) -> bool:
        return self.status in {"recusada", "revisao_manual"}


def _zero_limit_rejection() -> ReviewEvaluation:
    return ReviewEvaluation(
        status="recusada",
        reasons=(
            Reason(
                code="limite_zero_nao_reembolsavel",
                description="A política define limite zero para esta categoria.",
            ),
        ),
    )


def _manual_review(description: str) -> ReviewEvaluation:
    return ReviewEvaluation(
        status="revisao_manual",
        reasons=(
            Reason(
                code="revisao_manual_viagem",
                description=description,
            ),
        ),
    )


def evaluate_manual_review(
    expense: Expense,
    rule: CategoryRule,
    travel_days: Set[date],
    current_status: str | None = None,
    current_reasons: tuple[Reason, ...] = (),
) -> ReviewEvaluation:
    """Apply zero-limit precedence and the travel review conditions."""

    if current_status is not None:
        return ReviewEvaluation(status=current_status, reasons=current_reasons)

    if rule.limit == Decimal("0"):
        return _zero_limit_rejection()

    if normalize_category(expense.category) == "hospedagem":
        return _manual_review(
            "Hospedagem requer revisão manual porque as diárias são indetermináveis."
        )

    if travel_days and expense.date not in travel_days:
        return _manual_review(
            "A data da despesa não foi identificada como dia de viagem."
        )

    return ReviewEvaluation()
