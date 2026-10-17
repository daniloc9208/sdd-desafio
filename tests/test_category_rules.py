from datetime import date
from decimal import Decimal

from reembolso.category_rules import evaluate_category
from reembolso.models import CategoryRule, Expense, Policy


def _rule(limit: str = "60.00") -> CategoryRule:
    return CategoryRule(
        limit=Decimal(limit),
        periodicity="dia",
        observation=None,
    )


def _policy() -> Policy:
    return Policy(
        version="v4",
        effective_date=date(2026, 7, 1),
        base_currency="BRL",
        default_rules={
            "alimentacao": _rule(),
            "hospedagem": _rule("300.00"),
        },
        cost_center_rules={"cc-comercial": {"representacao": _rule("250.00")}},
        receipt_threshold=Decimal("100.00"),
        travel_increase_percent=Decimal("50"),
    )


def _expense(category: str, *, has_receipt: bool = True) -> Expense:
    return Expense(
        id="d-001",
        date=date(2026, 7, 7),
        category=category,
        description="Despesa",
        supplier="Fornecedor",
        original_value=Decimal("100.00"),
        original_currency="BRL",
        has_receipt=has_receipt,
    )


def test_rn007_categoria_maiuscula() -> None:
    evaluation = evaluate_category(_expense("ALIMENTACAO"), _policy(), "CC-1")

    assert evaluation.normalized_category == "alimentacao"
    assert not evaluation.rejected


def test_rn007_categoria_com_espacos() -> None:
    evaluation = evaluate_category(_expense(" hospedagem "), _policy(), "CC-1")

    assert evaluation.normalized_category == "hospedagem"
    assert not evaluation.rejected


def test_rn007_categoria_fora_politica() -> None:
    evaluation = evaluate_category(_expense("coworking"), _policy(), "CC-1")

    assert evaluation.rejected
    assert tuple(reason.code for reason in evaluation.reasons) == (
        "categoria_fora_politica",
    )


def test_rn007_categoria_especifica_por_centro() -> None:
    evaluation = evaluate_category(_expense("representacao"), _policy(), "CC-COMERCIAL")

    assert evaluation.rule is not None
    assert evaluation.rule.limit == Decimal("250.00")


def test_rn007_representacao_sem_regra() -> None:
    evaluation = evaluate_category(_expense("representacao"), _policy(), "CC-1")

    assert evaluation.rejected
    assert evaluation.rule is None


def test_rn007_motivo_legivel() -> None:
    evaluation = evaluate_category(_expense("coworking"), _policy(), "CC-1")

    assert "fora da política" in evaluation.reasons[0].description


def test_rn007_recusa_encerra_item() -> None:
    rejected = evaluate_category(
        _expense("desconhecida", has_receipt=False),
        _policy(),
        "CC-1",
    )
    next_expense = evaluate_category(_expense("alimentacao"), _policy(), "CC-1")

    assert tuple(reason.code for reason in rejected.reasons) == (
        "categoria_fora_politica",
    )
    assert not next_expense.rejected
