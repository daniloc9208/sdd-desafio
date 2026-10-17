from datetime import date
from decimal import Decimal

from reembolso.models import CategoryRule, Expense, Reason
from reembolso.review_rules import evaluate_manual_review


def _rule(limit: str = "100.00", observation: str | None = None) -> CategoryRule:
    return CategoryRule(
        limit=Decimal(limit),
        periodicity="dia",
        observation=observation,
    )


def _expense(
    category: str,
    expense_date: date = date(2026, 7, 18),
) -> Expense:
    return Expense(
        id="d-001",
        date=expense_date,
        category=category,
        description="Despesa",
        supplier="Fornecedor",
        original_value=Decimal("50.00"),
        original_currency="BRL",
        has_receipt=True,
    )


def test_rn004_hospedagem_revisao_manual() -> None:
    result = evaluate_manual_review(
        _expense("hospedagem"),
        _rule("300.00"),
        {date(2026, 7, 19)},
    )

    assert result.status == "revisao_manual"
    assert tuple(reason.code for reason in result.reasons) == ("revisao_manual_viagem",)


def test_rn012_limite_zero_recusa_antes_de_revisao() -> None:
    with_marker = evaluate_manual_review(
        _expense("hospedagem"),
        _rule("0.00", "nao reembolsavel"),
        {date(2026, 7, 19)},
    )
    without_marker = evaluate_manual_review(
        _expense("hospedagem"),
        _rule("0"),
        {date(2026, 7, 19)},
    )

    for result in (with_marker, without_marker):
        assert result.status == "recusada"
        assert tuple(reason.code for reason in result.reasons) == (
            "limite_zero_nao_reembolsavel",
        )


def test_rn004_descricao_distingue_causa() -> None:
    lodging = evaluate_manual_review(
        _expense("hospedagem"),
        _rule("300.00"),
        {date(2026, 7, 19)},
    )
    outside_trip_day = evaluate_manual_review(
        _expense("alimentacao"),
        _rule(),
        {date(2026, 7, 15), date(2026, 7, 23)},
    )

    assert lodging.reasons[0].description != outside_trip_day.reasons[0].description
    assert "diárias" in lodging.reasons[0].description
    assert "não foi identificada" in outside_trip_day.reasons[0].description


def test_rn004_data_nao_identificada_revisao_manual() -> None:
    result = evaluate_manual_review(
        _expense("alimentacao", date(2026, 7, 18)),
        _rule(),
        {date(2026, 7, 15), date(2026, 7, 23)},
    )

    assert result.status == "revisao_manual"
    assert tuple(reason.code for reason in result.reasons) == ("revisao_manual_viagem",)


def test_rn004_recusa_prevalece_sobre_revisao_manual() -> None:
    prior_reason = Reason(code="prazo_excedido", description="Prazo excedido.")

    result = evaluate_manual_review(
        _expense("alimentacao"),
        _rule(),
        {date(2026, 7, 15)},
        current_status="recusada",
        current_reasons=(prior_reason,),
    )

    assert result.status == "recusada"
    assert result.reasons == (prior_reason,)


def test_rn004_sem_hospedagem_sem_revisao_manual() -> None:
    result = evaluate_manual_review(
        _expense("alimentacao"),
        _rule(),
        set(),
    )

    assert result.status is None
    assert result.reasons == ()
