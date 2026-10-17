"""Strict JSON input parsing for expense batches."""

import json
import re
from datetime import date
from decimal import Decimal
from pathlib import Path
from types import MappingProxyType
from typing import Any

from reembolso.errors import InputDataError
from reembolso.models import Expense, InputBatch


def _reject_constant(value: str) -> None:
    raise ValueError(f"constante JSON não finita: {value}")


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"propriedade JSON repetida: {key}")
        result[key] = value
    return result


def read_json(path: Path, label: str) -> Any:
    try:
        with path.open("r", encoding="utf-8") as source:
            return json.load(
                source,
                parse_float=Decimal,
                parse_int=Decimal,
                parse_constant=_reject_constant,
                object_pairs_hook=_unique_object,
            )
    except json.JSONDecodeError as error:
        raise InputDataError(
            f"{label}: JSON inválido na linha {error.lineno}, "
            f"coluna {error.colno}: {error.msg}"
        ) from error
    except (OSError, UnicodeError, ValueError) as error:
        raise InputDataError(
            f"{label}: não foi possível ler JSON válido: {error}"
        ) from error


def _object(
    value: Any,
    label: str,
    required: set[str],
    optional: set[str] | None = None,
) -> dict[str, Any]:
    if optional is None:
        optional = set()
    if not isinstance(value, dict):
        raise InputDataError(f"{label}: deve ser um objeto JSON")
    missing = required - value.keys()
    extra = value.keys() - required - optional
    if missing:
        raise InputDataError(
            f"{label}: campo obrigatório ausente: {sorted(missing)[0]}"
        )
    if extra:
        raise InputDataError(f"{label}: propriedade não permitida: {sorted(extra)[0]}")
    return value


def _text(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise InputDataError(f"{label}: deve ser uma string não vazia")
    return value


def _valid_date(value: Any, label: str) -> date:
    if not isinstance(value, str):
        raise InputDataError(f"{label}: deve estar no formato AAAA-MM-DD")
    try:
        parsed = date.fromisoformat(value)
    except ValueError as error:
        raise InputDataError(f"{label}: data inválida: {value}") from error
    if parsed.isoformat() != value:
        raise InputDataError(f"{label}: deve estar no formato AAAA-MM-DD")
    return parsed


def _money(value: Any, label: str) -> Decimal:
    if not isinstance(value, Decimal) or not value.is_finite():
        raise InputDataError(f"{label}: deve ser um número decimal finito")
    return value


def load_expenses(path: Path) -> InputBatch:
    document = _object(
        read_json(path, "Arquivo de despesas"),
        "raiz",
        {"colaborador", "periodo", "despesas"},
    )
    collaborator_raw = _object(
        document["colaborador"],
        "colaborador",
        {"id", "nome", "centro_custo"},
    )
    collaborator = {
        field: _text(collaborator_raw[field], f"colaborador.{field}")
        for field in ("id", "nome", "centro_custo")
    }

    period_raw = _object(
        document["periodo"],
        "periodo",
        {"competencia", "inicio", "fim"},
    )
    competence = _text(period_raw["competencia"], "periodo.competencia")
    if not re.fullmatch(r"\d{4}-(0[1-9]|1[0-2])", competence):
        raise InputDataError("periodo.competencia: deve estar no formato AAAA-MM")
    start = _valid_date(period_raw["inicio"], "periodo.inicio")
    end = _valid_date(period_raw["fim"], "periodo.fim")
    if start.strftime("%Y-%m") != competence:
        raise InputDataError("periodo.inicio deve pertencer à competencia")
    if end < start:
        raise InputDataError("periodo.fim não pode ser anterior a periodo.inicio")
    period = {
        "competencia": competence,
        "inicio": start.isoformat(),
        "fim": end.isoformat(),
    }

    raw_expenses = document["despesas"]
    if not isinstance(raw_expenses, list):
        raise InputDataError("despesas: deve ser uma lista")
    expenses: list[Expense] = []
    identifiers: set[str] = set()
    for index, raw_expense in enumerate(raw_expenses):
        label = f"despesas[{index}]"
        raw = _object(
            raw_expense,
            label,
            {
                "id",
                "data",
                "categoria",
                "descricao",
                "fornecedor",
                "valor",
                "tem_nota_fiscal",
            },
            {"moeda"},
        )
        expense_id = _text(raw["id"], f"{label}.id")
        normalized_id = expense_id.strip()
        if normalized_id in identifiers:
            raise InputDataError(
                f"{label}.id: identificador duplicado: {normalized_id}"
            )
        identifiers.add(normalized_id)

        currency = raw.get("moeda", "BRL")
        if (
            not isinstance(currency, str)
            or len(currency) != 3
            or not all("A" <= character <= "Z" for character in currency)
        ):
            raise InputDataError(
                f"{label}.moeda: deve ser um código ISO 4217 de três letras maiúsculas"
            )
        has_receipt = raw["tem_nota_fiscal"]
        if not isinstance(has_receipt, bool):
            raise InputDataError(f"{label}.tem_nota_fiscal: deve ser booleano")

        expenses.append(
            Expense(
                id=expense_id,
                date=_valid_date(raw["data"], f"{label}.data"),
                category=_text(raw["categoria"], f"{label}.categoria"),
                description=_text(raw["descricao"], f"{label}.descricao"),
                supplier=_text(raw["fornecedor"], f"{label}.fornecedor"),
                original_value=_money(raw["valor"], f"{label}.valor"),
                original_currency=currency,
                has_receipt=has_receipt,
            )
        )

    return InputBatch(
        collaborator=MappingProxyType(collaborator),
        period=MappingProxyType(period),
        expenses=tuple(expenses),
    )
