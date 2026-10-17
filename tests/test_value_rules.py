from datetime import date
from decimal import Decimal

from reembolso.models import Expense
from reembolso.value_rules import validate_expense_value


def _expense(identifier: str, value: str) -> Expense:
    return Expense(
        id=identifier,
        date=date(2026, 7, 15),
        category="alimentacao",
        description="Almoço",
        supplier="Restaurante",
        original_value=Decimal(value),
        original_currency="BRL",
        has_receipt=True,
    )


def test_rn008_valor_zero() -> None:
    result = validate_expense_value(_expense("d-zero", "0"), Decimal("0"))

    assert result.rejected
    assert result.terminal
    assert tuple(reason.code for reason in result.reasons) == ("valor_zero_invalido",)


def test_rn008_valor_negativo() -> None:
    expenses = (
        _expense("d-009", "-45.00"),
        _expense("d-valida", "25.00"),
    )

    results = tuple(
        validate_expense_value(expense, expense.original_value) for expense in expenses
    )

    assert results[0].rejected
    assert tuple(reason.code for reason in results[0].reasons) == (
        "valor_negativo_fora_escopo",
    )
    assert not results[1].rejected
    assert results[1].reasons == ()


def test_rn008_valor_subcentavo_0_004() -> None:
    result = validate_expense_value(_expense("d-sub", "0.004"), Decimal("0.004"))

    assert result.rejected
    assert result.terminal
    assert tuple(reason.code for reason in result.reasons) == (
        "valor_inferior_ao_centavo",
    )


def test_rn008_valor_subcentavo_fronteira_0_005() -> None:
    result = validate_expense_value(_expense("d-meio", "0.005"), Decimal("0.005"))

    assert not result.rejected
    assert not result.terminal
    assert result.reasons == ()


def test_rn008_recusa_encerra_item() -> None:
    rejected = validate_expense_value(_expense("d-zero", "0"), Decimal("0"))
    valid = validate_expense_value(_expense("d-valida", "10.00"), Decimal("10.00"))
    later_rule_calls: list[str] = []

    for expense, result in zip(
        (_expense("d-zero", "0"), _expense("d-valida", "10.00")),
        (rejected, valid),
        strict=True,
    ):
        if result.terminal:
            continue
        later_rule_calls.append(expense.id)

    assert later_rule_calls == ["d-valida"]
    assert tuple(reason.code for reason in rejected.reasons) == ("valor_zero_invalido",)


def test_rn008_subcentavo_usa_equivalente_brl_sem_arredondar_retorno() -> None:
    expense = _expense("d-eur", "0.001")

    result = validate_expense_value(expense, Decimal("0.005"))

    assert not result.rejected


def test_rn008_cotacao_ausente_nao_e_recusada_por_esta_regra() -> None:
    result = validate_expense_value(_expense("d-gbp", "1.00"), None)

    assert not result.rejected
    assert result.reasons == ()
