import copy
import json
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest

from reembolso.errors import InputDataError
from reembolso.input_data import load_expenses

EXAMPLE_PATH = Path(__file__).parents[1] / "exemplos" / "despesas-exemplo.json"


@pytest.fixture
def valid_document() -> dict[str, Any]:
    return {
        "colaborador": {
            "id": "c-001",
            "nome": "Ana",
            "centro_custo": "CC-ENG",
        },
        "periodo": {
            "competencia": "2026-07",
            "inicio": "2026-07-01",
            "fim": "2026-07-31",
        },
        "despesas": [
            {
                "id": "d-001",
                "data": "2026-07-03",
                "categoria": "alimentacao",
                "descricao": "Almoço",
                "fornecedor": "Restaurante",
                "valor": 72.5,
                "tem_nota_fiscal": True,
            }
        ],
    }


def write_document(tmp_path: Path, document: dict[str, Any]) -> Path:
    path = tmp_path / "despesas.json"
    path.write_text(json.dumps(document, ensure_ascii=False), encoding="utf-8")
    return path


def test_parser_valido() -> None:
    batch = load_expenses(EXAMPLE_PATH)

    assert len(batch.expenses) == 14


def test_parser_moeda_ausente_default_brl(
    tmp_path: Path, valid_document: dict[str, Any]
) -> None:
    batch = load_expenses(write_document(tmp_path, valid_document))

    assert batch.expenses[0].original_currency == "BRL"


def test_parser_moeda_estrangeira(
    tmp_path: Path, valid_document: dict[str, Any]
) -> None:
    valid_document["despesas"][0]["moeda"] = "XYZ"
    valid_document["despesas"][0]["valor"] = 12.34

    expense = load_expenses(write_document(tmp_path, valid_document)).expenses[0]

    assert expense.original_currency == "XYZ"
    assert expense.original_value == Decimal("12.34")
    assert isinstance(expense.original_value, Decimal)


def test_parser_inteiro_vira_decimal(
    tmp_path: Path, valid_document: dict[str, Any]
) -> None:
    valid_document["despesas"][0]["valor"] = 100

    value = (
        load_expenses(write_document(tmp_path, valid_document))
        .expenses[0]
        .original_value
    )

    assert value == Decimal("100")
    assert type(value) is Decimal


def test_parser_campo_ausente(tmp_path: Path, valid_document: dict[str, Any]) -> None:
    del valid_document["colaborador"]["id"]

    with pytest.raises(InputDataError, match="campo obrigatório ausente: id"):
        load_expenses(write_document(tmp_path, valid_document))


@pytest.mark.parametrize(
    ("object_name", "field", "kind"),
    [
        ("raiz", "periodo", "missing"),
        ("raiz", "extra", "extra"),
        ("colaborador", "nome", "missing"),
        ("colaborador", "extra", "extra"),
        ("periodo", "fim", "missing"),
        ("periodo", "extra", "extra"),
        ("despesa", "fornecedor", "missing"),
        ("despesa", "extra", "extra"),
    ],
)
def test_parser_objetos_com_campos_ausentes_ou_extras(
    tmp_path: Path,
    valid_document: dict[str, Any],
    object_name: str,
    field: str,
    kind: str,
) -> None:
    target = {
        "raiz": valid_document,
        "colaborador": valid_document["colaborador"],
        "periodo": valid_document["periodo"],
        "despesa": valid_document["despesas"][0],
    }[object_name]
    if kind == "missing":
        del target[field]
    else:
        target[field] = "não permitido"

    with pytest.raises(InputDataError):
        load_expenses(write_document(tmp_path, valid_document))


def test_parser_rejeita_chave_json_repetida(tmp_path: Path) -> None:
    path = tmp_path / "repetida.json"
    path.write_text(
        '{"colaborador": {}, "colaborador": {}, "periodo": {}, "despesas": []}',
        encoding="utf-8",
    )

    with pytest.raises(InputDataError, match="propriedade JSON repetida"):
        load_expenses(path)


def test_parser_propriedade_extra_raiz(
    tmp_path: Path, valid_document: dict[str, Any]
) -> None:
    valid_document["extra"] = True

    with pytest.raises(InputDataError, match="propriedade não permitida: extra"):
        load_expenses(write_document(tmp_path, valid_document))


def test_parser_propriedade_extra_colaborador(
    tmp_path: Path, valid_document: dict[str, Any]
) -> None:
    valid_document["colaborador"]["extra"] = True

    with pytest.raises(InputDataError, match="propriedade não permitida: extra"):
        load_expenses(write_document(tmp_path, valid_document))


def test_parser_propriedade_extra_periodo(
    tmp_path: Path, valid_document: dict[str, Any]
) -> None:
    valid_document["periodo"]["extra"] = True

    with pytest.raises(InputDataError, match="propriedade não permitida: extra"):
        load_expenses(write_document(tmp_path, valid_document))


def test_parser_propriedade_extra_despesa(
    tmp_path: Path, valid_document: dict[str, Any]
) -> None:
    valid_document["despesas"][0]["extra"] = True

    with pytest.raises(InputDataError, match="propriedade não permitida: extra"):
        load_expenses(write_document(tmp_path, valid_document))


def test_parser_id_repetido(tmp_path: Path, valid_document: dict[str, Any]) -> None:
    duplicate = copy.deepcopy(valid_document["despesas"][0])
    duplicate["id"] = " d-001 "
    valid_document["despesas"].append(duplicate)

    with pytest.raises(InputDataError, match="identificador duplicado: d-001"):
        load_expenses(write_document(tmp_path, valid_document))


def test_parser_data_invalida(tmp_path: Path, valid_document: dict[str, Any]) -> None:
    valid_document["despesas"][0]["data"] = "2026-02-30"

    with pytest.raises(InputDataError, match="data inválida"):
        load_expenses(write_document(tmp_path, valid_document))


def test_parser_valor_nao_finito(
    tmp_path: Path, valid_document: dict[str, Any]
) -> None:
    serialized = json.dumps(valid_document, ensure_ascii=False).replace(
        "72.5", "Infinity"
    )
    path = tmp_path / "nao-finito.json"
    path.write_text(serialized, encoding="utf-8")

    with pytest.raises(InputDataError, match="constante JSON não finita: Infinity"):
        load_expenses(path)


def test_parser_decimal_preservado(
    tmp_path: Path, valid_document: dict[str, Any]
) -> None:
    first = valid_document["despesas"][0]
    first["valor"] = 54.90
    second = copy.deepcopy(first)
    second["id"] = "d-002"
    second["valor"] = 54.9
    second["descricao"] = "Jantar"
    valid_document["despesas"].append(second)

    path = write_document(tmp_path, valid_document)
    serialized = path.read_text(encoding="utf-8")
    path.write_text(serialized.replace("54.9", "54.90", 1), encoding="utf-8")
    values = [expense.original_value for expense in load_expenses(path).expenses]

    assert values == [Decimal("54.9"), Decimal("54.9")]
    assert values[0].as_tuple().exponent == -2
    assert values[1].as_tuple().exponent == -1
    assert all(type(value) is Decimal for value in values)
