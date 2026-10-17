"""Strict loading and validation for historical exchange-rate files."""

import re
from datetime import date
from decimal import Decimal
from pathlib import Path
from types import MappingProxyType
from typing import Any

from reembolso.errors import InputDataError
from reembolso.input_data import read_json
from reembolso.models import ExchangeRates

_ROOT_FIELDS = {"moeda_base", "taxas"}
_ROOT_OPTIONAL_FIELDS = {"fonte", "observacao"}
_CURRENCY_PATTERN = re.compile(r"[A-Z]{3}", re.ASCII)
_DATE_PATTERN = re.compile(r"\d{4}-\d{2}-\d{2}", re.ASCII)


def _exact_root(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise InputDataError("câmbio: deve ser um objeto JSON")
    missing = _ROOT_FIELDS - value.keys()
    extra = value.keys() - _ROOT_FIELDS - _ROOT_OPTIONAL_FIELDS
    if missing:
        raise InputDataError(f"câmbio: campo obrigatório ausente: {sorted(missing)[0]}")
    if extra:
        raise InputDataError(f"câmbio: propriedade não permitida: {sorted(extra)[0]}")
    return value


def _strict_date(value: Any, label: str) -> date:
    if not isinstance(value, str) or not _DATE_PATTERN.fullmatch(value):
        raise InputDataError(f"{label}: deve estar no formato AAAA-MM-DD")
    try:
        parsed = date.fromisoformat(value)
    except ValueError as error:
        raise InputDataError(f"{label}: data inválida: {value}") from error
    if parsed.isoformat() != value:
        raise InputDataError(f"{label}: deve estar no formato AAAA-MM-DD")
    return parsed


def _validate_metadata(document: dict[str, Any]) -> None:
    for field in _ROOT_OPTIONAL_FIELDS:
        if field in document:
            value = document[field]
            if not isinstance(value, str) or not value.strip():
                raise InputDataError(f"câmbio.{field}: deve ser uma string não vazia")


def _load_rates(value: Any) -> MappingProxyType:
    if not isinstance(value, dict):
        raise InputDataError("câmbio.taxas: deve ser um objeto JSON")

    rates_by_date: dict[date, MappingProxyType] = {}
    for raw_date, raw_rates in value.items():
        rate_date = _strict_date(raw_date, "câmbio.taxas: data")
        if not isinstance(raw_rates, dict):
            raise InputDataError(f"câmbio.taxas.{raw_date}: deve ser um objeto JSON")

        daily_rates: dict[str, Decimal] = {}
        for currency, rate in raw_rates.items():
            if not isinstance(currency, str) or not _CURRENCY_PATTERN.fullmatch(
                currency
            ):
                raise InputDataError(
                    f"câmbio.taxas.{raw_date}: moeda deve ter três letras "
                    "ASCII maiúsculas"
                )
            if (
                not isinstance(rate, Decimal)
                or not rate.is_finite()
                or rate <= Decimal("0")
            ):
                raise InputDataError(
                    f"câmbio.taxas.{raw_date}.{currency}: taxa deve ser um "
                    "número decimal finito positivo"
                )
            if currency == "BRL" and rate != Decimal("1"):
                raise InputDataError(
                    f"câmbio.taxas.{raw_date}.BRL: taxa deve ser igual a 1"
                )
            daily_rates[currency] = rate

        rates_by_date[rate_date] = MappingProxyType(daily_rates)

    return MappingProxyType(rates_by_date)


def load_exchange_rates(path: Path) -> ExchangeRates:
    """Load historical rates from a UTF-8 JSON file without external access."""

    document = _exact_root(read_json(path, "Arquivo de câmbio"))
    if document["moeda_base"] != "BRL":
        raise InputDataError("câmbio.moeda_base: deve ser BRL")
    _validate_metadata(document)
    return ExchangeRates(
        base_currency="BRL",
        rates=_load_rates(document["taxas"]),
    )
