import copy
import json
from datetime import date
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest

from reembolso.errors import InputDataError
from reembolso.policy_data import load_policy

POLICY_PATH = Path(__file__).parents[1] / "exemplos" / "envelope" / "politica-v4.json"


@pytest.fixture
def valid_policy_document() -> dict[str, Any]:
    return json.loads(POLICY_PATH.read_text(encoding="utf-8"))


def write_policy(tmp_path: Path, document: dict[str, Any]) -> Path:
    path = tmp_path / "politica.json"
    path.write_text(json.dumps(document, ensure_ascii=False), encoding="utf-8")
    return path


def test_policy_v4_valida() -> None:
    policy = load_policy(POLICY_PATH, date(2026, 7, 31))

    assert policy.version == "v4"
    assert policy.effective_date == date(2026, 7, 1)
    assert policy.base_currency == "BRL"
    assert policy.receipt_threshold == Decimal("100.00")
    assert policy.travel_increase_percent == Decimal("50")
    assert policy.default_rules["alimentacao"].limit == Decimal("60.00")


def test_policy_rejeita_limite_negativo(
    tmp_path: Path, valid_policy_document: dict[str, Any]
) -> None:
    valid_policy_document["padrao"]["alimentacao"]["limite"] = -0.01

    with pytest.raises(InputDataError, match="não negativo"):
        load_policy(write_policy(tmp_path, valid_policy_document), date(2026, 7, 31))


def test_policy_rejeita_categoria_vazia(
    tmp_path: Path, valid_policy_document: dict[str, Any]
) -> None:
    rule = valid_policy_document["padrao"].pop("alimentacao")
    valid_policy_document["padrao"]["   "] = rule

    with pytest.raises(InputDataError, match="string não vazia"):
        load_policy(write_policy(tmp_path, valid_policy_document), date(2026, 7, 31))


@pytest.mark.parametrize("level", ["raiz", "regra"])
def test_policy_rejeita_propriedade_extra(
    tmp_path: Path, valid_policy_document: dict[str, Any], level: str
) -> None:
    target = (
        valid_policy_document
        if level == "raiz"
        else valid_policy_document["padrao"]["alimentacao"]
    )
    target["extra"] = True

    with pytest.raises(InputDataError, match="propriedade não permitida: extra"):
        load_policy(write_policy(tmp_path, valid_policy_document), date(2026, 7, 31))


def test_policy_rejeita_chave_json_repetida(tmp_path: Path) -> None:
    path = tmp_path / "politica-repetida.json"
    path.write_text(
        '{"versao":"v4","versao":"v5","vigencia":"2026-07-01",'
        '"moeda_base":"BRL","padrao":{},"centros_custo":{},'
        '"nota_fiscal_obrigatoria_acima_de":100,'
        '"acrescimo_em_viagem_percentual":50}',
        encoding="utf-8",
    )

    with pytest.raises(InputDataError, match="propriedade JSON repetida"):
        load_policy(path, date(2026, 7, 31))


def test_policy_rejeita_vigencia_futura(
    tmp_path: Path, valid_policy_document: dict[str, Any]
) -> None:
    valid_policy_document["vigencia"] = "2026-08-01"

    with pytest.raises(InputDataError, match="ainda não vigente"):
        load_policy(write_policy(tmp_path, valid_policy_document), date(2026, 7, 31))


def test_policy_rejeita_marcador_com_limite_positivo(
    tmp_path: Path, valid_policy_document: dict[str, Any]
) -> None:
    rule = valid_policy_document["padrao"]["hospedagem"]
    rule["observacao"] = " NAO REEMBOLSAVEL "

    with pytest.raises(InputDataError, match="exige limite zero"):
        load_policy(write_policy(tmp_path, valid_policy_document), date(2026, 7, 31))


def test_policy_rejeita_observacao_nula(
    tmp_path: Path, valid_policy_document: dict[str, Any]
) -> None:
    valid_policy_document["padrao"]["alimentacao"]["observacao"] = None

    with pytest.raises(InputDataError, match="string não vazia"):
        load_policy(write_policy(tmp_path, valid_policy_document), date(2026, 7, 31))


def test_policy_aceita_rotulo_versao_desconhecido(
    tmp_path: Path, valid_policy_document: dict[str, Any]
) -> None:
    valid_policy_document["versao"] = "formato-futuro"

    policy = load_policy(
        write_policy(tmp_path, valid_policy_document), date(2026, 7, 31)
    )

    assert policy.version == "formato-futuro"


@pytest.mark.parametrize("version", ["", "   "])
def test_policy_rejeita_versao_vazia(
    tmp_path: Path, valid_policy_document: dict[str, Any], version: str
) -> None:
    valid_policy_document["versao"] = version

    with pytest.raises(InputDataError, match="string não vazia"):
        load_policy(write_policy(tmp_path, valid_policy_document), date(2026, 7, 31))


@pytest.mark.parametrize("empty_key", ["centro", "categoria"])
def test_policy_rejeita_chave_vazia(
    tmp_path: Path, valid_policy_document: dict[str, Any], empty_key: str
) -> None:
    if empty_key == "centro":
        rules = valid_policy_document["centros_custo"].pop("CC-ADM")
        valid_policy_document["centros_custo"]["  "] = rules
    else:
        rule = valid_policy_document["padrao"].pop("alimentacao")
        valid_policy_document["padrao"]["  "] = rule

    with pytest.raises(InputDataError, match="string não vazia"):
        load_policy(write_policy(tmp_path, valid_policy_document), date(2026, 7, 31))


def test_policy_chaves_centros_colidem(
    tmp_path: Path, valid_policy_document: dict[str, Any]
) -> None:
    valid_policy_document["centros_custo"][" cc-adm "] = copy.deepcopy(
        valid_policy_document["centros_custo"]["CC-ADM"]
    )

    with pytest.raises(InputDataError, match="centros colidem"):
        load_policy(write_policy(tmp_path, valid_policy_document), date(2026, 7, 31))


def test_policy_chaves_categorias_colidem(
    tmp_path: Path, valid_policy_document: dict[str, Any]
) -> None:
    valid_policy_document["padrao"][" ALIMENTACAO "] = copy.deepcopy(
        valid_policy_document["padrao"]["alimentacao"]
    )

    with pytest.raises(InputDataError, match="categorias colidem"):
        load_policy(write_policy(tmp_path, valid_policy_document), date(2026, 7, 31))


def test_policy_nao_reembolsavel_preservada() -> None:
    policy = load_policy(POLICY_PATH, date(2026, 7, 31))

    rule = policy.cost_center_rules["cc-eng-plataforma"]["hospedagem"]
    assert rule.limit == Decimal("0.00")
    assert rule.observation == "nao reembolsavel"
    assert rule.explicitly_non_reimbursable


def test_policy_cria_tabelas_imutaveis() -> None:
    policy = load_policy(POLICY_PATH, date(2026, 7, 31))

    with pytest.raises(TypeError):
        policy.default_rules["nova"] = policy.default_rules["alimentacao"]
    with pytest.raises(TypeError):
        policy.cost_center_rules["cc-adm"]["nova"] = policy.default_rules["alimentacao"]
