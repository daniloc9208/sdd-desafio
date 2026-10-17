import json
import socket
from datetime import date
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest

from reembolso.errors import InputDataError
from reembolso.exchange_rate_data import load_exchange_rates

EXCHANGE_RATES_PATH = (
    Path(__file__).parents[1] / "exemplos" / "envelope" / "cambio.json"
)


@pytest.fixture
def valid_exchange_rates_document() -> dict[str, Any]:
    return json.loads(EXCHANGE_RATES_PATH.read_text(encoding="utf-8"))


def write_exchange_rates(tmp_path: Path, document: Any) -> Path:
    path = tmp_path / "cambio.json"
    path.write_text(json.dumps(document, ensure_ascii=False), encoding="utf-8")
    return path


def test_exchange_rates_valida_cambio_envelope() -> None:
    exchange_rates = load_exchange_rates(EXCHANGE_RATES_PATH)

    assert exchange_rates.base_currency == "BRL"
    assert exchange_rates.rates[date(2026, 7, 14)]["EUR"] == Decimal("5.93")
    assert isinstance(exchange_rates.rates[date(2026, 7, 14)]["EUR"], Decimal)


def test_cotacao_exata_usa_fechamento() -> None:
    exchange_rates = load_exchange_rates(EXCHANGE_RATES_PATH)

    assert exchange_rates.rate_for("EUR", date(2026, 7, 14)) == Decimal("5.93")


def test_cotacao_fim_de_semana_usa_ultima_anterior() -> None:
    exchange_rates = load_exchange_rates(EXCHANGE_RATES_PATH)

    assert exchange_rates.rate_for("EUR", date(2026, 7, 18)) == Decimal("5.96")


def test_cotacao_nao_usa_data_futura() -> None:
    exchange_rates = load_exchange_rates(EXCHANGE_RATES_PATH)

    assert exchange_rates.rate_for("EUR", date(2026, 7, 12)) is None


def test_moeda_sem_cotacao_retorna_ausencia() -> None:
    exchange_rates = load_exchange_rates(EXCHANGE_RATES_PATH)

    assert exchange_rates.rate_for("GBP", date(2026, 7, 31)) is None


def test_brl_usa_taxa_unitaria_implicita() -> None:
    exchange_rates = load_exchange_rates(EXCHANGE_RATES_PATH)

    assert exchange_rates.rate_for("BRL", date(2026, 7, 14)) == Decimal("1")


def test_cotacao_busca_ultima_data_que_contem_a_moeda(tmp_path: Path) -> None:
    path = write_exchange_rates(
        tmp_path,
        {
            "moeda_base": "BRL",
            "taxas": {
                "2026-07-16": {"EUR": 5.90},
                "2026-07-17": {"USD": 5.47},
            },
        },
    )

    exchange_rates = load_exchange_rates(path)

    assert exchange_rates.rate_for("EUR", date(2026, 7, 18)) == Decimal("5.9")


def test_cotacao_nao_consulta_rede(monkeypatch: pytest.MonkeyPatch) -> None:
    def fail_network(*args: object, **kwargs: object) -> None:
        raise AssertionError("consulta de rede não permitida")

    monkeypatch.setattr(socket, "create_connection", fail_network)
    exchange_rates = load_exchange_rates(EXCHANGE_RATES_PATH)

    assert exchange_rates.rate_for("GBP", date(2026, 7, 31)) is None


def test_exchange_rates_rejeita_chave_json_repetida(tmp_path: Path) -> None:
    path = tmp_path / "cambio-repetido.json"
    path.write_text(
        '{"moeda_base":"BRL","taxas":{"2026-07-14":{"EUR":5.93,"EUR":5.94}}}',
        encoding="utf-8",
    )

    with pytest.raises(InputDataError, match="propriedade JSON repetida"):
        load_exchange_rates(path)


def test_exchange_rates_aceita_brl_unitario(
    tmp_path: Path, valid_exchange_rates_document: dict[str, Any]
) -> None:
    valid_exchange_rates_document["taxas"]["2026-07-14"]["BRL"] = 1

    exchange_rates = load_exchange_rates(
        write_exchange_rates(tmp_path, valid_exchange_rates_document)
    )

    assert exchange_rates.rate_for("BRL", date(2026, 7, 14)) == Decimal("1")
    assert exchange_rates.rate_for("BRL", date(1900, 1, 1)) == Decimal("1")


def test_exchange_rates_rejeita_brl_nao_unitario(
    tmp_path: Path, valid_exchange_rates_document: dict[str, Any]
) -> None:
    valid_exchange_rates_document["taxas"]["2026-07-14"]["BRL"] = 1.01

    with pytest.raises(InputDataError, match="taxa deve ser igual a 1"):
        load_exchange_rates(
            write_exchange_rates(tmp_path, valid_exchange_rates_document)
        )


@pytest.mark.parametrize(
    ("mutate", "message"),
    [
        (lambda document: document.update(extra=True), "propriedade não permitida"),
        (lambda document: document.pop("taxas"), "campo obrigatório ausente"),
        (lambda document: document.update(moeda_base="USD"), "deve ser BRL"),
        (lambda document: document.update(taxas=[]), "deve ser um objeto JSON"),
        (
            lambda document: document["taxas"].update({"2026-02-30": {}}),
            "data inválida",
        ),
        (
            lambda document: document["taxas"].update({"2026-7-1": {}}),
            "formato AAAA-MM-DD",
        ),
        (
            lambda document: document["taxas"].update({"2026-07-30": []}),
            "deve ser um objeto JSON",
        ),
        (
            lambda document: document["taxas"]["2026-07-14"].update(eur=1),
            "três letras ASCII maiúsculas",
        ),
        (
            lambda document: document["taxas"]["2026-07-14"].update(EURO=1),
            "três letras ASCII maiúsculas",
        ),
        (
            lambda document: document["taxas"]["2026-07-14"].update(EUR=0),
            "finito positivo",
        ),
        (
            lambda document: document["taxas"]["2026-07-14"].update(EUR=-1),
            "finito positivo",
        ),
        (
            lambda document: document["taxas"]["2026-07-14"].update(EUR="5.93"),
            "finito positivo",
        ),
        (
            lambda document: document["taxas"]["2026-07-14"].update(EUR=True),
            "finito positivo",
        ),
        (lambda document: document.update(fonte="  "), "string não vazia"),
        (lambda document: document.update(observacao=None), "string não vazia"),
    ],
    ids=[
        "campo-extra",
        "campo-ausente",
        "moeda-base",
        "taxas-nao-objeto",
        "data-impossivel",
        "data-formato",
        "dia-nao-objeto",
        "codigo-minusculo",
        "codigo-quatro-letras",
        "taxa-zero",
        "taxa-negativa",
        "taxa-string",
        "taxa-booleana",
        "fonte-vazia",
        "observacao-tipo",
    ],
)
def test_exchange_rates_rejeita_schema_ou_taxas_invalidos(
    tmp_path: Path,
    valid_exchange_rates_document: dict[str, Any],
    mutate: Any,
    message: str,
) -> None:
    mutate(valid_exchange_rates_document)

    with pytest.raises(InputDataError, match=message):
        load_exchange_rates(
            write_exchange_rates(tmp_path, valid_exchange_rates_document)
        )


def test_exchange_rates_cria_tabelas_imutaveis() -> None:
    exchange_rates = load_exchange_rates(EXCHANGE_RATES_PATH)

    with pytest.raises(TypeError):
        exchange_rates.rates[date(2026, 7, 14)]["GBP"] = Decimal("6.80")
    with pytest.raises(TypeError):
        exchange_rates.rates[date(2026, 7, 30)] = {}
