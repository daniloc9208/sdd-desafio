"""Strict loading and validation for reimbursement policy files."""

from collections.abc import Callable
from datetime import date
from decimal import Decimal
from pathlib import Path
from types import MappingProxyType
from typing import Any

from reembolso.errors import InputDataError
from reembolso.input_data import read_json
from reembolso.models import CategoryRule, Policy

_POLICY_FIELDS = {
    "versao",
    "vigencia",
    "moeda_base",
    "padrao",
    "centros_custo",
    "nota_fiscal_obrigatoria_acima_de",
    "acrescimo_em_viagem_percentual",
}
_RULE_FIELDS = {"limite", "periodicidade"}
_RULE_OPTIONAL_FIELDS = {"observacao"}
_PERIODICITIES = {"dia", "diaria"}


def _exact_object(
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


def _non_empty_text(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise InputDataError(f"{label}: deve ser uma string não vazia")
    return value


def _strict_date(value: Any, label: str) -> date:
    if not isinstance(value, str):
        raise InputDataError(f"{label}: deve estar no formato AAAA-MM-DD")
    try:
        parsed = date.fromisoformat(value)
    except ValueError as error:
        raise InputDataError(f"{label}: data inválida: {value}") from error
    if parsed.isoformat() != value:
        raise InputDataError(f"{label}: deve estar no formato AAAA-MM-DD")
    return parsed


def _non_negative_decimal(value: Any, label: str) -> Decimal:
    if not isinstance(value, Decimal) or not value.is_finite() or value < Decimal("0"):
        raise InputDataError(f"{label}: deve ser um número decimal finito não negativo")
    return value


def _normalized_key(value: Any, label: str, normalize: Callable[[str], str]) -> str:
    text = _non_empty_text(value, label)
    normalized = normalize(text)
    if not normalized:
        raise InputDataError(f"{label}: chave vazia após normalização")
    return normalized


def _load_rule(value: Any, label: str) -> CategoryRule:
    raw = _exact_object(value, label, _RULE_FIELDS, _RULE_OPTIONAL_FIELDS)
    limit = _non_negative_decimal(raw["limite"], f"{label}.limite")
    periodicity = raw["periodicidade"]
    if not isinstance(periodicity, str) or periodicity not in _PERIODICITIES:
        raise InputDataError(f"{label}.periodicidade: deve ser 'dia' ou 'diaria'")

    observation = None
    if "observacao" in raw:
        observation_raw = raw["observacao"]
        observation = _non_empty_text(observation_raw, f"{label}.observacao")
        if observation.strip().casefold() == "nao reembolsavel" and limit != Decimal(
            "0"
        ):
            raise InputDataError(
                f"{label}: observacao 'nao reembolsavel' exige limite zero"
            )

    return CategoryRule(
        limit=limit,
        periodicity=periodicity,
        observation=observation,
    )


def _load_rule_table(value: Any, label: str) -> MappingProxyType:
    if not isinstance(value, dict):
        raise InputDataError(f"{label}: deve ser um objeto JSON")
    rules: dict[str, CategoryRule] = {}
    original_keys: dict[str, str] = {}
    for raw_category, raw_rule in value.items():
        category = _normalized_key(
            raw_category,
            f"{label}: categoria",
            lambda text: text.strip().lower(),
        )
        if category in rules:
            raise InputDataError(
                f"{label}: categorias colidem após normalização: "
                f"{original_keys[category]!r} e {raw_category!r}"
            )
        rules[category] = _load_rule(raw_rule, f"{label}.{raw_category}")
        original_keys[category] = raw_category
    return MappingProxyType(rules)


def load_policy(path: Path, calculation_date: date) -> Policy:
    """Load a policy valid on ``calculation_date`` from a UTF-8 JSON file."""

    document = _exact_object(
        read_json(path, "Arquivo de política"),
        "política",
        _POLICY_FIELDS,
    )
    version = _non_empty_text(document["versao"], "política.versao")
    effective_date = _strict_date(document["vigencia"], "política.vigencia")
    if calculation_date < effective_date:
        raise InputDataError(
            "política.vigencia: política ainda não vigente em data_calculo"
        )
    if document["moeda_base"] != "BRL":
        raise InputDataError("política.moeda_base: deve ser BRL")

    default_rules = _load_rule_table(document["padrao"], "política.padrao")
    raw_centers = document["centros_custo"]
    if not isinstance(raw_centers, dict):
        raise InputDataError("política.centros_custo: deve ser um objeto JSON")

    center_rules: dict[str, MappingProxyType] = {}
    original_centers: dict[str, str] = {}
    for raw_center, raw_rules in raw_centers.items():
        center = _normalized_key(
            raw_center,
            "política.centros_custo: centro de custo",
            lambda text: text.strip().casefold(),
        )
        if center in center_rules:
            raise InputDataError(
                "política.centros_custo: centros colidem após normalização: "
                f"{original_centers[center]!r} e {raw_center!r}"
            )
        center_rules[center] = _load_rule_table(
            raw_rules, f"política.centros_custo.{raw_center}"
        )
        original_centers[center] = raw_center

    return Policy(
        version=version,
        effective_date=effective_date,
        base_currency="BRL",
        default_rules=default_rules,
        cost_center_rules=MappingProxyType(center_rules),
        receipt_threshold=_non_negative_decimal(
            document["nota_fiscal_obrigatoria_acima_de"],
            "política.nota_fiscal_obrigatoria_acima_de",
        ),
        travel_increase_percent=_non_negative_decimal(
            document["acrescimo_em_viagem_percentual"],
            "política.acrescimo_em_viagem_percentual",
        ),
    )
