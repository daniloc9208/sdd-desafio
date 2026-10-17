from datetime import date
from decimal import Decimal

from reembolso.models import Expense, Policy
from reembolso.receipt_rules import evaluate_receipt_requirement


def _policy(threshold: str = "100.00") -> Policy:
    return Policy(
        version="v4",
        effective_date=date(2026, 7, 1),
        base_currency="BRL",
        default_rules={},
        cost_center_rules={},
        receipt_threshold=Decimal(threshold),
        travel_increase_percent=Decimal("50"),
    )


def _expense(
    identifier: str,
    value: str,
    *,
    currency: str = "BRL",
    has_receipt: bool = False,
) -> Expense:
    return Expense(
        id=identifier,
        date=date(2026, 7, 15),
        category="transporte",
        description="Despesa",
        supplier="Fornecedor",
        original_value=Decimal(value),
        original_currency=currency,
        has_receipt=has_receipt,
    )


def test_rn003_exato_100_sem_nota() -> None:
    result = evaluate_receipt_requirement(
        _expense("d-003", "100.00"),
        Decimal("100.00"),
        _policy(),
    )

    assert result.rejected
    assert result.terminal
    assert tuple(reason.code for reason in result.reasons) == ("nota_fiscal_ausente",)


def test_rn003_acima_100_sem_nota() -> None:
    result = evaluate_receipt_requirement(
        _expense("d-004", "100.01"),
        Decimal("100.01"),
        _policy(),
    )

    assert result.rejected
    assert result.terminal
    assert tuple(reason.code for reason in result.reasons) == ("nota_fiscal_ausente",)


def test_rn003_abaixo_100_sem_nota() -> None:
    result = evaluate_receipt_requirement(
        _expense("d-abaixo", "99.99"),
        Decimal("99.99"),
        _policy(),
    )

    assert not result.rejected
    assert not result.terminal
    assert result.reasons == ()


def test_rn003_exato_100_com_nota() -> None:
    result = evaluate_receipt_requirement(
        _expense("d-com-nota", "100.00", has_receipt=True),
        Decimal("100.00"),
        _policy(),
    )

    assert not result.rejected
    assert not result.terminal
    assert result.reasons == ()


def test_rn003_conversao_antes_do_limite() -> None:
    expense = _expense("d-eur", "16.863", currency="EUR")

    result = evaluate_receipt_requirement(
        expense,
        Decimal("100.00759"),
        _policy(),
    )

    assert result.rejected
    assert tuple(reason.code for reason in result.reasons) == ("nota_fiscal_ausente",)


def test_rn003_nao_arredonda_equivalente_antes_da_comparacao() -> None:
    result = evaluate_receipt_requirement(
        _expense("d-fronteira", "99.999"),
        Decimal("99.999"),
        _policy(),
    )

    assert not result.rejected
    assert result.reasons == ()


def test_rn003_recusa_encerra_item() -> None:
    expenses_and_values = (
        (_expense("d-sem-nota", "100.00"), Decimal("100.00")),
        (_expense("d-valida", "25.00"), Decimal("25.00")),
    )
    later_rule_calls: list[str] = []

    for expense, reported_value in expenses_and_values:
        result = evaluate_receipt_requirement(expense, reported_value, _policy())
        if result.terminal:
            continue
        later_rule_calls.append(expense.id)

    assert later_rule_calls == ["d-valida"]


def test_rn003_usa_limite_carregado_da_politica() -> None:
    result = evaluate_receipt_requirement(
        _expense("d-limite-configurado", "80.00"),
        Decimal("80.00"),
        _policy("75.00"),
    )

    assert result.rejected


def test_rn003_equivalente_ausente_nao_adiciona_segunda_recusa() -> None:
    result = evaluate_receipt_requirement(
        _expense("d-sem-cotacao", "100.00", currency="GBP"),
        None,
        _policy(),
    )

    assert not result.rejected
    assert result.reasons == ()
