from datetime import date
from decimal import Decimal

from reembolso.deadline_rules import validate_expense_deadline
from reembolso.models import Expense


def _expense(identifier: str, expense_date: date) -> Expense:
    return Expense(
        id=identifier,
        date=expense_date,
        category="alimentacao",
        description="Despesa",
        supplier="Fornecedor",
        original_value=Decimal("25.00"),
        original_currency="BRL",
        has_receipt=True,
    )


def test_rn005_prazo_exato_90_dias() -> None:
    result = validate_expense_deadline(
        _expense("d-90", date(2026, 7, 17)),
        date(2026, 10, 15),
    )

    assert not result.rejected
    assert not result.terminal
    assert result.reasons == ()


def test_rn005_prazo_91_dias() -> None:
    result = validate_expense_deadline(
        _expense("d-91", date(2026, 7, 16)),
        date(2026, 10, 15),
    )

    assert result.rejected
    assert result.terminal
    assert tuple(reason.code for reason in result.reasons) == ("prazo_excedido",)


def test_rn005_data_hoje() -> None:
    calculation_date = date(2026, 10, 15)

    result = validate_expense_deadline(
        _expense("d-hoje", calculation_date),
        calculation_date,
    )

    assert not result.rejected
    assert not result.terminal
    assert result.reasons == ()


def test_rn005_data_futura() -> None:
    result = validate_expense_deadline(
        _expense("d-futura", date(2026, 10, 16)),
        date(2026, 10, 15),
    )

    assert result.rejected
    assert result.terminal
    assert tuple(reason.code for reason in result.reasons) == ("data_futura",)


def test_rn005_d008_excede_prazo() -> None:
    expense = _expense("d-008", date(2026, 4, 15))

    result = validate_expense_deadline(expense, date(2026, 7, 31))

    assert (date(2026, 7, 31) - expense.date).days == 107
    assert result.rejected
    assert tuple(reason.code for reason in result.reasons) == ("prazo_excedido",)


def test_rn005_recusa_encerra_apenas_o_item() -> None:
    expenses = (
        _expense("d-futura", date(2026, 8, 1)),
        _expense("d-valida", date(2026, 7, 31)),
    )
    calculation_date = date(2026, 7, 31)
    evaluated_by_later_rule: list[str] = []

    results = tuple(
        validate_expense_deadline(expense, calculation_date) for expense in expenses
    )
    for expense, result in zip(expenses, results, strict=True):
        if result.terminal:
            continue
        evaluated_by_later_rule.append(expense.id)

    assert evaluated_by_later_rule == ["d-valida"]
    assert tuple(reason.code for reason in results[0].reasons) == ("data_futura",)
    assert not results[1].rejected
