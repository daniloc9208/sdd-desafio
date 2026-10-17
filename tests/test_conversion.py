from datetime import date
from decimal import Decimal
from pathlib import Path

from reembolso.conversion import convert_expense_to_brl
from reembolso.input_data import load_expenses
from reembolso.models import ExchangeRates, Expense


def _expense(
    *,
    value: str = "10.123456789123456789123456789",
    currency: str = "EUR",
    expense_date: date = date(2026, 7, 18),
) -> Expense:
    return Expense(
        id="e-001",
        date=expense_date,
        category="alimentacao",
        description="Almoço",
        supplier="Restaurante",
        original_value=Decimal(value),
        original_currency=currency,
        has_receipt=True,
    )


def _rates() -> ExchangeRates:
    return ExchangeRates(
        base_currency="BRL",
        rates={
            date(2026, 7, 16): {"EUR": Decimal("5.90")},
            date(2026, 7, 17): {"EUR": Decimal("5.96")},
        },
    )


def test_conversao_multiplica_decimal_sem_float() -> None:
    expense = _expense()

    conversion = convert_expense_to_brl(expense, _rates())

    assert conversion.reported_value == Decimal("60.33580246317580246317580246244")
    assert isinstance(conversion.reported_value, Decimal)
    assert conversion.status is None
    assert conversion.reasons == ()


def test_moeda_ausente_equivale_brl(tmp_path: Path) -> None:
    path = tmp_path / "despesas.json"
    path.write_text(
        """{
            "colaborador": {
                "id": "c-001",
                "nome": "Ana",
                "centro_custo": "CC-1"
            },
            "periodo": {
                "competencia": "2026-07",
                "inicio": "2026-07-01",
                "fim": "2026-07-31"
            },
            "despesas": [{
                "id": "e-001",
                "data": "2026-07-18",
                "categoria": "alimentacao",
                "descricao": "Almoço",
                "fornecedor": "Restaurante",
                "valor": 72.505,
                "tem_nota_fiscal": true
            }]
        }""",
        encoding="utf-8",
    )
    expense = load_expenses(path).expenses[0]

    conversion = convert_expense_to_brl(expense, _rates())

    assert expense.original_currency == "BRL"
    assert conversion.reported_value == Decimal("72.505")
    assert conversion.status is None


def test_cotacao_ausente_recusa_item_com_valor_nulo() -> None:
    expense = _expense(currency="GBP")

    conversion = convert_expense_to_brl(expense, _rates())

    assert conversion.reported_value is None
    assert conversion.rejected
    assert conversion.status == "recusada"
    assert tuple(reason.code for reason in conversion.reasons) == (
        "cotacao_indisponivel",
    )


def test_conversao_preserva_valor_moeda_originais() -> None:
    expense = _expense(value="10.00", currency="EUR")

    conversion = convert_expense_to_brl(expense, _rates())

    assert conversion.reported_value == Decimal("59.6000")
    assert conversion.original_value == Decimal("10.00")
    assert conversion.original_currency == "EUR"


def test_valor_informado_convertido_em_despesa_recusada() -> None:
    # Other rules may reject this negative item, but its auditable BRL value remains.
    expense = _expense(value="-10.00", currency="EUR")

    conversion = convert_expense_to_brl(expense, _rates())

    assert conversion.reported_value == Decimal("-59.6000")
