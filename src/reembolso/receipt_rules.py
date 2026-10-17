"""Receipt requirement for expenses according to RN-003."""

from dataclasses import dataclass
from decimal import Decimal

from reembolso.models import Expense, Policy, Reason


@dataclass(frozen=True)
class ReceiptEvaluation:
    """Outcome of the receipt requirement, suitable for item short-circuiting."""

    status: str | None = None
    reasons: tuple[Reason, ...] = ()

    @property
    def rejected(self) -> bool:
        """Whether the missing receipt rejects the expense."""

        return self.status == "recusada"

    @property
    def terminal(self) -> bool:
        """Whether subsequent rules must be skipped for this expense."""

        return self.rejected


def evaluate_receipt_requirement(
    expense: Expense,
    reported_value: Decimal | None,
    policy: Policy,
) -> ReceiptEvaluation:
    """Apply RN-003 using the unrounded BRL equivalent.

    A missing BRL equivalent is handled earlier by the conversion rule. This
    function therefore does not add another rejection when ``reported_value``
    is ``None``.
    """

    if (
        reported_value is not None
        and reported_value >= policy.receipt_threshold
        and not expense.has_receipt
    ):
        return ReceiptEvaluation(
            status="recusada",
            reasons=(
                Reason(
                    code="nota_fiscal_ausente",
                    description=(
                        "Nota fiscal obrigatória não informada para despesa "
                        "que atingiu o limite da política."
                    ),
                ),
            ),
        )

    return ReceiptEvaluation()
