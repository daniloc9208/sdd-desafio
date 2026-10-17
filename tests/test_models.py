from datetime import date
from decimal import Decimal

from reembolso.models import (
    CalculationResult,
    CategoryRule,
    ExchangeRates,
    Expense,
    ExpenseDecision,
    InputBatch,
    Policy,
    Reason,
)


def test_models_instantiation() -> None:
    expense = Expense(
        id="d-001",
        date=date(2026, 7, 3),
        category="ALIMENTACAO",
        description="Almoço",
        supplier="Restaurante",
        original_value=Decimal("72.50"),
        original_currency="BRL",
        has_receipt=True,
        normalized_category="alimentacao",
    )
    batch = InputBatch(
        collaborator={"id": "c-001", "nome": "Ana", "centro_custo": "CC-1"},
        period={
            "competencia": "2026-07",
            "inicio": "2026-07-01",
            "fim": "2026-07-31",
        },
        expenses=(expense,),
    )
    category_rule = CategoryRule(
        limit=Decimal("75.00"),
        periodicity="por_despesa",
        observation=None,
    )
    policy = Policy(
        version="4",
        effective_date=date(2026, 1, 1),
        base_currency="BRL",
        default_rules={"alimentacao": category_rule},
        cost_center_rules={},
        receipt_threshold=Decimal("100.00"),
        travel_increase_percent=Decimal("20"),
    )
    exchange_rates = ExchangeRates(
        base_currency="BRL",
        rates={date(2026, 7, 3): {"USD": Decimal("5.50")}},
    )
    decision = ExpenseDecision(
        id=expense.id,
        status="reembolsada",
        reported_value=Decimal("72.50"),
        original_value=expense.original_value,
        original_currency=expense.original_currency,
        reimbursable_value=Decimal("72.50"),
        reasons=(Reason(code="dentro_limite", description="Dentro do limite."),),
    )
    result = CalculationResult(
        schema_version="2.0",
        calculation_date=date(2026, 7, 31),
        currency="BRL",
        collaborator=batch.collaborator,
        period=batch.period,
        expenses=(decision,),
        reimbursable_total=Decimal("72.50"),
        review_total=Decimal("0.00"),
    )

    assert isinstance(expense.original_value, Decimal)
    assert isinstance(category_rule.limit, Decimal)
    assert isinstance(policy.receipt_threshold, Decimal)
    assert isinstance(policy.travel_increase_percent, Decimal)
    assert isinstance(exchange_rates.rates[date(2026, 7, 3)]["USD"], Decimal)
    assert isinstance(decision.reported_value, Decimal)
    assert isinstance(decision.reimbursable_value, Decimal)
    assert isinstance(result.reimbursable_total, Decimal)
    assert isinstance(result.review_total, Decimal)
    assert not any(
        isinstance(value, float)
        for value in (
            expense.original_value,
            category_rule.limit,
            policy.receipt_threshold,
            policy.travel_increase_percent,
            decision.reported_value,
            decision.reimbursable_value,
            result.reimbursable_total,
            result.review_total,
        )
    )
