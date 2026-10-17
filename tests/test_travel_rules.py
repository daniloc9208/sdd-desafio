from datetime import date
from decimal import Decimal
from pathlib import Path

from reembolso.input_data import load_expenses
from reembolso.models import Expense
from reembolso.travel_rules import identify_travel_days

EXAMPLE_PATH = Path(__file__).parents[1] / "exemplos" / "despesas-exemplo.json"


def _expense(
    expense_id: str,
    expense_date: date,
    *,
    category: str = "hospedagem",
    value: str = "100.00",
    has_receipt: bool = True,
) -> Expense:
    return Expense(
        id=expense_id,
        date=expense_date,
        category=category,
        description="Despesa",
        supplier="Fornecedor",
        original_value=Decimal(value),
        original_currency="BRL",
        has_receipt=has_receipt,
    )


def test_rn004_hospedagem_gera_dia_seguinte() -> None:
    expense = _expense("d-010", date(2026, 7, 14))

    assert identify_travel_days((expense,)) == frozenset({date(2026, 7, 15)})


def test_rn004_duas_hospedagens_geram_dois_dias() -> None:
    batch = load_expenses(EXAMPLE_PATH)

    assert identify_travel_days(batch.expenses) == frozenset(
        {date(2026, 7, 15), date(2026, 7, 23)}
    )


def test_rn004_hospedagem_sem_nota_ainda_gera_dia() -> None:
    expense = _expense(
        "d-013",
        date(2026, 7, 22),
        value="690.00",
        has_receipt=False,
    )

    assert date(2026, 7, 23) in identify_travel_days((expense,))


def test_rn004_hospedagem_sem_regra_ativa_dia_viagem() -> None:
    lodging_without_applicable_policy = _expense("d-001", date(2026, 7, 20))

    assert identify_travel_days((lodging_without_applicable_policy,)) == frozenset(
        {date(2026, 7, 21)}
    )


def test_rn004_sem_hospedagem_conjunto_vazio() -> None:
    expense = _expense(
        "d-001",
        date(2026, 7, 20),
        category="alimentacao",
    )

    assert identify_travel_days((expense,)) == frozenset()


def test_rn004_datas_repetidas_dia_unico() -> None:
    expenses = (
        _expense("d-001", date(2026, 7, 20)),
        _expense("d-002", date(2026, 7, 20)),
    )

    assert identify_travel_days(expenses) == frozenset({date(2026, 7, 21)})
