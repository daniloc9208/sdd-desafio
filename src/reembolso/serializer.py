"""JSON serialization for calculation results."""

import json
from decimal import Decimal

from reembolso.models import CalculationResult, ExpenseDecision, Reason


def _format_brl(value: Decimal) -> str:
    """Format an already-rounded BRL value without changing its amount."""
    formatted = format(value, ".2f")
    if Decimal(formatted) != value:
        raise ValueError("valor monetario deve estar arredondado para duas casas")
    return formatted


def _serialize_reason(reason: Reason) -> dict[str, str]:
    return {"codigo": reason.code, "descricao": reason.description}


def _serialize_expense(decision: ExpenseDecision) -> dict[str, object]:
    reported_value = (
        None
        if decision.reported_value is None
        else _format_brl(decision.reported_value)
    )
    return {
        "id": decision.id,
        "status": decision.status,
        "valor_informado": reported_value,
        "valor_original": format(decision.original_value, "f"),
        "moeda_original": decision.original_currency,
        "valor_reembolsavel": _format_brl(decision.reimbursable_value),
        "motivos": [_serialize_reason(reason) for reason in decision.reasons],
    }


def serialize_result(result: CalculationResult) -> str:
    """Convert a calculation result to UTF-8-compatible JSON text."""
    document = {
        "versao_schema": result.schema_version,
        "data_calculo": result.calculation_date.isoformat(),
        "moeda": result.currency,
        "colaborador": dict(result.collaborator),
        "periodo": dict(result.period),
        "despesas": [_serialize_expense(expense) for expense in result.expenses],
        "totais": {
            "valor_reembolsavel": _format_brl(result.reimbursable_total),
            "valor_em_revisao": _format_brl(result.review_total),
        },
    }
    return json.dumps(document, ensure_ascii=False, indent=2)
