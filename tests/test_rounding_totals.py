"""Tests for monetary rounding and totals calculation (T-014 / RN-009)."""

from datetime import date
from decimal import Decimal

from reembolso.engine import calculate
from reembolso.models import (
    CategoryRule,
    ExchangeRates,
    Expense,
    InputBatch,
    Policy,
)
from reembolso.rounding import round_brl

# ---------------------------------------------------------------------------
# Unit tests for the round_brl function
# ---------------------------------------------------------------------------


def test_rn009_arredondamento_para_baixo() -> None:
    assert round_brl(Decimal("33.333")) == Decimal("33.33")


def test_rn009_arredondamento_para_cima() -> None:
    assert round_brl(Decimal("33.335")) == Decimal("33.34")


def test_rn009_arredondamento_exato_nao_altera() -> None:
    assert round_brl(Decimal("33.33")) == Decimal("33.33")


def test_rn009_arredondamento_zero() -> None:
    assert round_brl(Decimal("0")) == Decimal("0.00")


# ---------------------------------------------------------------------------
# Integration-level: totals via calculate()
# ---------------------------------------------------------------------------


def _simple_policy(food_limit: str = "60") -> Policy:
    return Policy(
        version="teste",
        effective_date=date(2026, 1, 1),
        base_currency="BRL",
        default_rules={
            "alimentacao": CategoryRule(
                limit=Decimal(food_limit),
                periodicity="dia",
                observation=None,
            ),
        },
        cost_center_rules={},
        receipt_threshold=Decimal("100"),
        travel_increase_percent=Decimal("50"),
    )


def _brl_rates() -> ExchangeRates:
    return ExchangeRates(base_currency="BRL", rates={})


def _expense(
    expense_id: str,
    value: str,
    *,
    expense_date: date = date(2026, 7, 15),
    has_receipt: bool = True,
) -> Expense:
    return Expense(
        id=expense_id,
        date=expense_date,
        category="alimentacao",
        description="Teste",
        supplier="Fornecedor",
        original_value=Decimal(value),
        original_currency="BRL",
        has_receipt=has_receipt,
    )


def _batch(*expenses: Expense) -> InputBatch:
    return InputBatch(
        collaborator={"id": "c-001", "nome": "Teste", "centro_custo": "CC-OUTRO"},
        period={"competencia": "2026-07", "inicio": "2026-07-01", "fim": "2026-07-31"},
        expenses=expenses,
    )


def test_rn009_total_soma_arredondados() -> None:
    """Total must be the sum of per-item rounded values, not the unrounded sum."""
    # Two expenses of 33.333 BRL each (different suppliers, no duplicate detection).
    # Unrounded sum = 66.666; sum of per-item rounded = 33.33 + 33.33 = 66.66.
    exp1 = Expense(
        id="d-001",
        date=date(2026, 7, 15),
        category="alimentacao",
        description="Refeicao A",
        supplier="Restaurante A",
        original_value=Decimal("33.333"),
        original_currency="BRL",
        has_receipt=True,
    )
    exp2 = Expense(
        id="d-002",
        date=date(2026, 7, 15),
        category="alimentacao",
        description="Refeicao B",
        supplier="Restaurante B",
        original_value=Decimal("33.333"),
        original_currency="BRL",
        has_receipt=True,
    )
    result = calculate(
        _batch(exp1, exp2), _simple_policy("60"), _brl_rates(), date(2026, 7, 31)
    )

    assert result.reimbursable_total == Decimal("66.66")


def test_rn009_total_em_revisao() -> None:
    """valor_em_revisao sums the rounded reported_value of ALL revisao_manual items."""
    hospedagem_rule = CategoryRule(
        limit=Decimal("250"),
        periodicity="diaria",
        observation=None,
    )
    policy = Policy(
        version="teste",
        effective_date=date(2026, 1, 1),
        base_currency="BRL",
        default_rules={
            "alimentacao": CategoryRule(
                limit=Decimal("60"), periodicity="dia", observation=None
            ),
            "hospedagem": hospedagem_rule,
        },
        cost_center_rules={},
        receipt_threshold=Decimal("100"),
        travel_increase_percent=Decimal("50"),
    )
    # Hospedagem goes to revisao_manual (indeterminate nights).
    # Meal on a non-travel date also goes to revisao_manual.
    # Both contribute to review_total.
    lodging = Expense(
        id="d-hsp",
        date=date(2026, 7, 14),
        category="hospedagem",
        description="Hotel",
        supplier="Hotel",
        original_value=Decimal("200"),
        original_currency="BRL",
        has_receipt=True,
    )
    meal = Expense(
        id="d-meal",
        date=date(2026, 7, 10),
        category="alimentacao",
        description="Almoco",
        supplier="Rest",
        original_value=Decimal("47.20"),
        original_currency="BRL",
        has_receipt=True,
    )
    batch = _batch(lodging, meal)
    result = calculate(batch, policy, _brl_rates(), date(2026, 7, 31))

    lodging_decision = next(d for d in result.expenses if d.id == "d-hsp")
    meal_decision = next(d for d in result.expenses if d.id == "d-meal")
    assert lodging_decision.status == "revisao_manual"
    assert meal_decision.status == "revisao_manual"
    assert meal_decision.reported_value == Decimal("47.20")
    # review_total = 200.00 (lodging) + 47.20 (meal)
    assert result.review_total == Decimal("247.20")


def test_rn009_reembolso_zero_quando_sem_aprovadas() -> None:
    """Total is 0.00 when all expenses are rejected."""
    expense = Expense(
        id="d-001",
        date=date(2026, 7, 15),
        category="coworking",  # not in policy
        description="Cowork",
        supplier="HubOffice",
        original_value=Decimal("50"),
        original_currency="BRL",
        has_receipt=True,
    )
    result = calculate(
        _batch(expense), _simple_policy(), _brl_rates(), date(2026, 7, 31)
    )

    assert result.reimbursable_total == Decimal("0")
    assert result.review_total == Decimal("0")
