"""Category normalization and policy-membership rule (RN-007)."""

from dataclasses import dataclass

from reembolso.models import CategoryRule, Expense, Policy, Reason


@dataclass(frozen=True)
class CategoryEvaluation:
    """Outcome of category validation before later expense rules."""

    normalized_category: str
    rule: CategoryRule | None
    status: str | None = None
    reasons: tuple[Reason, ...] = ()

    @property
    def rejected(self) -> bool:
        return self.status == "recusada"


def normalize_category(category: str) -> str:
    """Normalize a structurally valid category according to RN-007."""

    return category.strip().lower()


def evaluate_category(
    expense: Expense,
    policy: Policy,
    cost_center: str,
) -> CategoryEvaluation:
    """Resolve the expense category or reject it when no policy rule exists."""

    normalized_category = normalize_category(expense.category)
    rule = policy.rule_for(cost_center, normalized_category)
    if rule is None:
        return CategoryEvaluation(
            normalized_category=normalized_category,
            rule=None,
            status="recusada",
            reasons=(
                Reason(
                    code="categoria_fora_politica",
                    description=(
                        f"A categoria '{normalized_category}' está fora da política."
                    ),
                ),
            ),
        )

    return CategoryEvaluation(
        normalized_category=normalized_category,
        rule=rule,
    )
