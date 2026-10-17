from datetime import date
from decimal import Decimal

import pytest

from reembolso.limit_rules import apply_expense_limit
from reembolso.models import CategoryRule, Expense, Policy, Reason


def _rule(limit: str) -> CategoryRule:
    return CategoryRule(
        limit=Decimal(limit),
        periodicity="dia",
        observation=None,
    )


def _policy(
    *,
    food_limit: str = "60",
    transport_limit: str = "80",
    travel_percent: str = "50",
) -> Policy:
    return Policy(
        version="teste",
        effective_date=date(2026, 1, 1),
        base_currency="BRL",
        default_rules={
            "alimentacao": _rule(food_limit),
            "transporte": _rule(transport_limit),
        },
        cost_center_rules={
            "cc-especifico": {"alimentacao": _rule("70")},
        },
        receipt_threshold=Decimal("100"),
        travel_increase_percent=Decimal(travel_percent),
    )


def _expense(
    category: str,
    *,
    expense_id: str = "d-001",
    expense_date: date = date(2026, 7, 18),
) -> Expense:
    return Expense(
        id=expense_id,
        date=expense_date,
        category=category,
        description="Despesa",
        supplier="Fornecedor",
        original_value=Decimal("1"),
        original_currency="BRL",
        has_receipt=True,
    )


def _reason_codes(result: object) -> tuple[str, ...]:
    return tuple(reason.code for reason in result.reasons)  # type: ignore[attr-defined]


def test_rn001_alimentacao_abaixo_teto() -> None:
    result = apply_expense_limit(
        _expense("alimentacao"), Decimal("38.00"), _policy(), "CC-OUTRO", set()
    )

    assert result.status == "reembolsada"
    assert result.reimbursable_value == Decimal("38.00")
    assert _reason_codes(result) == ("dentro_do_limite",)


def test_rn001_alimentacao_acima_teto() -> None:
    result = apply_expense_limit(
        _expense("alimentacao"), Decimal("72.50"), _policy(), "CC-OUTRO", set()
    )

    assert result.status == "reembolsada_parcialmente"
    assert result.reimbursable_value == Decimal("60")
    assert _reason_codes(result) == ("limite_aplicado",)


def test_rn001_transporte_abaixo_teto() -> None:
    result = apply_expense_limit(
        _expense("transporte"), Decimal("75.00"), _policy(), "CC-OUTRO", set()
    )

    assert result.status == "reembolsada"
    assert result.reimbursable_value == Decimal("75.00")
    assert _reason_codes(result) == ("dentro_do_limite",)


def test_rn001_transporte_acima_teto() -> None:
    result = apply_expense_limit(
        _expense("transporte"), Decimal("100.00"), _policy(), "CC-OUTRO", set()
    )

    assert result.status == "reembolsada_parcialmente"
    assert result.reimbursable_value == Decimal("80")
    assert _reason_codes(result) == ("limite_aplicado",)


def test_rn004_viagem_abaixo_teto_ampliado() -> None:
    travel_day = date(2026, 7, 15)
    result = apply_expense_limit(
        _expense("alimentacao", expense_id="d-011", expense_date=travel_day),
        Decimal("33.333"),
        _policy(),
        "CC-OUTRO",
        {travel_day},
    )

    assert result.status == "reembolsada"
    assert result.reimbursable_value == Decimal("33.333")
    assert result.applied_limit == Decimal("90")
    assert _reason_codes(result) == (
        "limite_viagem_aplicado",
        "dentro_do_limite",
    )


def test_rn004_viagem_acima_teto_ampliado() -> None:
    travel_day = date(2026, 7, 15)
    result = apply_expense_limit(
        _expense("alimentacao", expense_date=travel_day),
        Decimal("100.00"),
        _policy(),
        "CC-OUTRO",
        {travel_day},
    )

    assert result.status == "reembolsada_parcialmente"
    assert result.reimbursable_value == Decimal("90")
    assert _reason_codes(result) == (
        "limite_viagem_aplicado",
        "limite_aplicado",
    )


def test_rn004_duas_despesas_mesmo_dia_viagem() -> None:
    travel_day = date(2026, 7, 15)
    results = tuple(
        apply_expense_limit(
            _expense("alimentacao", expense_id=expense_id, expense_date=travel_day),
            value,
            _policy(),
            "CC-OUTRO",
            {travel_day},
        )
        for expense_id, value in (
            ("d-001", Decimal("89")),
            ("d-002", Decimal("100")),
        )
    )

    assert tuple(result.applied_limit for result in results) == (
        Decimal("90"),
        Decimal("90"),
    )
    assert tuple(result.reimbursable_value for result in results) == (
        Decimal("89"),
        Decimal("90"),
    )


def test_rn006_motivos_nao_vazios() -> None:
    travel_day = date(2026, 7, 15)
    results = (
        apply_expense_limit(
            _expense("alimentacao"), Decimal("38"), _policy(), "CC-OUTRO", set()
        ),
        apply_expense_limit(
            _expense("alimentacao", expense_date=travel_day),
            Decimal("100"),
            _policy(),
            "CC-OUTRO",
            {travel_day},
        ),
    )

    assert all(result.reasons for result in results)


def test_rn012_regra_especifica_prevalece_e_categoria_usa_fallback() -> None:
    specific = apply_expense_limit(
        _expense("alimentacao"),
        Decimal("65"),
        _policy(),
        " CC-ESPECIFICO ",
        set(),
    )
    fallback = apply_expense_limit(
        _expense("transporte"),
        Decimal("75"),
        _policy(),
        "CC-ESPECIFICO",
        set(),
    )

    assert specific.status == "reembolsada"
    assert specific.applied_limit == Decimal("70")
    assert fallback.status == "reembolsada"
    assert fallback.applied_limit == Decimal("80")


@pytest.mark.parametrize("terminal_status", ["recusada", "revisao_manual"])
def test_passo_9_preserva_status_terminal_anterior(terminal_status: str) -> None:
    prior_reason = Reason(code="motivo_anterior", description="Tratado antes.")

    result = apply_expense_limit(
        _expense("alimentacao"),
        Decimal("1000"),
        _policy(),
        "CC-OUTRO",
        {date(2026, 7, 18)},
        current_status=terminal_status,
        current_reasons=(prior_reason,),
    )

    assert result.status == terminal_status
    assert result.reimbursable_value == Decimal("0")
    assert result.reasons == (prior_reason,)
    assert result.applied_limit is None


def test_passo_9_nao_arredonda_valores() -> None:
    result = apply_expense_limit(
        _expense("alimentacao"),
        Decimal("33.333"),
        _policy(),
        "CC-OUTRO",
        set(),
    )

    assert result.reimbursable_value == Decimal("33.333")


def test_rn004_data_repetida_nao_acumula_acrescimo() -> None:
    travel_day = date(2026, 7, 15)
    result = apply_expense_limit(
        _expense("alimentacao", expense_date=travel_day),
        Decimal("95"),
        _policy(),
        "CC-OUTRO",
        {travel_day},
    )

    assert result.applied_limit == Decimal("90")
    assert result.reimbursable_value == Decimal("90")
