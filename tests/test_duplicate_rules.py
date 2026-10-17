from datetime import date
from decimal import Decimal
from pathlib import Path

from reembolso.duplicate_rules import DuplicateDetector
from reembolso.input_data import load_expenses
from reembolso.models import Expense

EXAMPLE_PATH = Path(__file__).parents[1] / "exemplos" / "despesas-exemplo.json"


def _expense(
    expense_id: str,
    *,
    value: str = "54.90",
    currency: str = "BRL",
    supplier: str = "Bistro Central",
    category: str = "alimentacao",
) -> Expense:
    return Expense(
        id=expense_id,
        date=date(2026, 7, 9),
        category=category,
        description="Almoco",
        supplier=supplier,
        original_value=Decimal(value),
        original_currency=currency,
        has_receipt=True,
    )


def test_rn006_duplicata_basica() -> None:
    batch = load_expenses(EXAMPLE_PATH)
    expenses = tuple(
        expense for expense in batch.expenses if expense.id in {"d-006", "d-007"}
    )
    detector = DuplicateDetector()

    evaluations = tuple(detector.evaluate(expense) for expense in expenses)

    assert not evaluations[0].rejected
    assert evaluations[1].rejected
    assert tuple(reason.code for reason in evaluations[1].reasons) == ("duplicata",)


def test_rn006_valores_numericamente_iguais() -> None:
    detector = DuplicateDetector()

    first = detector.evaluate(_expense("d-001", value="54.90"))
    second = detector.evaluate(_expense("d-002", value="54.9"))

    assert not first.rejected
    assert second.rejected


def test_rn006_valores_distintos_mesmos_centavos() -> None:
    detector = DuplicateDetector()

    first = detector.evaluate(_expense("d-001", value="33.331"))
    second = detector.evaluate(_expense("d-002", value="33.334"))

    assert not first.rejected
    assert not second.rejected


def test_rn006_moedas_diferentes_nao_sao_duplicatas() -> None:
    detector = DuplicateDetector()

    first = detector.evaluate(_expense("d-001", value="10", currency="EUR"))
    second = detector.evaluate(_expense("d-002", value="10", currency="USD"))

    assert not first.rejected
    assert not second.rejected


def test_rn006_fornecedor_case_sensitive() -> None:
    detector = DuplicateDetector()

    first = detector.evaluate(_expense("d-001", supplier="Bistro Central"))
    second = detector.evaluate(_expense("d-002", supplier="BISTRO CENTRAL"))

    assert not first.rejected
    assert not second.rejected


def test_rn006_recusa_encerra_item() -> None:
    detector = DuplicateDetector()
    first = detector.evaluate(_expense("d-001"))
    duplicate = detector.evaluate(_expense("d-002", category="ALIMENTACAO"))
    later_rule_calls: list[str] = []

    for expense_id, evaluation in (("d-001", first), ("d-002", duplicate)):
        if evaluation.terminal:
            continue
        later_rule_calls.append(expense_id)

    assert later_rule_calls == ["d-001"]
    assert tuple(reason.code for reason in duplicate.reasons) == ("duplicata",)
