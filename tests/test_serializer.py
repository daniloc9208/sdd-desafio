import json
from datetime import date
from decimal import Decimal

import pytest

from reembolso.models import CalculationResult, ExpenseDecision, Reason
from reembolso.serializer import serialize_result


def _decision(
    *,
    expense_id: str = "d-001",
    reported_value: Decimal | None = Decimal("33.33"),
    original_value: Decimal = Decimal("33.3300"),
    original_currency: str = "BRL",
    reimbursable_value: Decimal = Decimal("33.33"),
) -> ExpenseDecision:
    return ExpenseDecision(
        id=expense_id,
        status="reembolsada",
        reported_value=reported_value,
        original_value=original_value,
        original_currency=original_currency,
        reimbursable_value=reimbursable_value,
        reasons=(
            Reason(
                code="dentro_do_limite",
                description="Valor dentro do limite aplicável.",
            ),
        ),
    )


def _result(
    *decisions: ExpenseDecision,
    reimbursable_total: Decimal = Decimal("33.33"),
    review_total: Decimal = Decimal("0.00"),
) -> CalculationResult:
    return CalculationResult(
        schema_version="2.0",
        calculation_date=date(2026, 10, 16),
        currency="BRL",
        collaborator={
            "id": "c-001",
            "nome": "João",
            "centro_custo": "CC-1",
        },
        period={
            "competencia": "2026-10",
            "inicio": "2026-10-01",
            "fim": "2026-10-31",
        },
        expenses=decisions,
        reimbursable_total=reimbursable_total,
        review_total=review_total,
    )


def _serialize(result: CalculationResult) -> dict[str, object]:
    return json.loads(serialize_result(result))


def test_serializador_decimal_ja_arredondado() -> None:
    document = _serialize(_result(_decision()))

    assert document["despesas"][0]["valor_informado"] == "33.33"
    assert document["totais"]["valor_em_revisao"] == "0.00"


def test_serializador_nao_aplica_arredondamento() -> None:
    result = _result(_decision(reimbursable_value=Decimal("33.333")))

    with pytest.raises(ValueError, match="arredondado para duas casas"):
        serialize_result(result)


def test_serializador_versao_schema() -> None:
    assert _serialize(_result(_decision()))["versao_schema"] == "2.0"


def test_serializador_moeda() -> None:
    assert _serialize(_result(_decision()))["moeda"] == "BRL"


def test_serializador_preserva_valor_e_moeda_originais() -> None:
    decision = _decision(
        reported_value=Decimal("179.55"),
        original_value=Decimal("33.2500"),
        original_currency="USD",
    )

    serialized = _serialize(_result(decision))["despesas"][0]

    assert serialized["valor_original"] == "33.2500"
    assert serialized["moeda_original"] == "USD"


def test_serializador_valor_informado_nulo() -> None:
    decision = _decision(reported_value=None, reimbursable_value=Decimal("0.00"))

    serialized = _serialize(_result(decision, reimbursable_total=Decimal("0.00")))[
        "despesas"
    ][0]

    assert serialized["valor_informado"] is None


def test_serializador_lote_vazio() -> None:
    document = _serialize(
        _result(
            reimbursable_total=Decimal("0.00"),
            review_total=Decimal("0.00"),
        )
    )

    assert document["despesas"] == []
    assert document["totais"] == {
        "valor_reembolsavel": "0.00",
        "valor_em_revisao": "0.00",
    }


def test_serializador_campos_exatos() -> None:
    document = _serialize(_result(_decision()))

    assert set(document) == {
        "versao_schema",
        "data_calculo",
        "moeda",
        "colaborador",
        "periodo",
        "despesas",
        "totais",
    }
    assert set(document["totais"]) == {
        "valor_reembolsavel",
        "valor_em_revisao",
    }
    assert set(document["despesas"][0]) == {
        "id",
        "status",
        "valor_informado",
        "valor_original",
        "moeda_original",
        "valor_reembolsavel",
        "motivos",
    }
    assert set(document["despesas"][0]["motivos"][0]) == {
        "codigo",
        "descricao",
    }


def test_serializador_preserva_ordem_entrada() -> None:
    decisions = (
        _decision(expense_id="d-003"),
        _decision(expense_id="d-001"),
        _decision(expense_id="d-002"),
    )

    serialized = _serialize(_result(*decisions, reimbursable_total=Decimal("99.99")))

    assert [expense["id"] for expense in serialized["despesas"]] == [
        "d-003",
        "d-001",
        "d-002",
    ]
