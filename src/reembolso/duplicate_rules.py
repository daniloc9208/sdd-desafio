"""Sequential duplicate detection for expenses (RN-006)."""

from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from reembolso.category_rules import normalize_category
from reembolso.models import Expense, Reason

DuplicateKey = tuple[str, date, Decimal, str, str, str]


@dataclass(frozen=True)
class DuplicateEvaluation:
    """Outcome of duplicate detection for one otherwise eligible item."""

    status: str | None = None
    reasons: tuple[Reason, ...] = ()

    @property
    def rejected(self) -> bool:
        return self.status == "recusada"

    @property
    def terminal(self) -> bool:
        return self.rejected


class DuplicateDetector:
    """Remember the first occurrence of each normative duplicate key."""

    def __init__(self) -> None:
        self._seen: set[DuplicateKey] = set()

    @staticmethod
    def key_for(expense: Expense) -> DuplicateKey:
        return (
            normalize_category(expense.category),
            expense.date,
            expense.original_value,
            expense.original_currency,
            expense.description,
            expense.supplier,
        )

    def evaluate(self, expense: Expense) -> DuplicateEvaluation:
        """Keep the first key occurrence and reject every later occurrence."""

        key = self.key_for(expense)
        if key in self._seen:
            return DuplicateEvaluation(
                status="recusada",
                reasons=(
                    Reason(
                        code="duplicata",
                        description="Despesa duplicada em relação a item anterior.",
                    ),
                ),
            )
        self._seen.add(key)
        return DuplicateEvaluation()
