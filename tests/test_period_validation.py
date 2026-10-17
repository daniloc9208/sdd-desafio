import json
from pathlib import Path

import pytest

from reembolso.errors import InputDataError
from reembolso.input_data import load_expenses


def _write_batch(tmp_path: Path, *, competence: str, start: str, end: str) -> Path:
    document = {
        "colaborador": {
            "id": "c-001",
            "nome": "Ana",
            "centro_custo": "CC-ENG",
        },
        "periodo": {
            "competencia": competence,
            "inicio": start,
            "fim": end,
        },
        "despesas": [],
    }
    path = tmp_path / "despesas.json"
    path.write_text(json.dumps(document), encoding="utf-8")
    return path


def test_rn011_inicio_fora_competencia(tmp_path: Path) -> None:
    path = _write_batch(
        tmp_path,
        competence="2026-07",
        start="2026-06-30",
        end="2026-07-31",
    )

    with pytest.raises(InputDataError, match="inicio deve pertencer à competencia"):
        load_expenses(path)


def test_rn011_fim_anterior_ao_inicio(tmp_path: Path) -> None:
    path = _write_batch(
        tmp_path,
        competence="2026-07",
        start="2026-07-15",
        end="2026-07-14",
    )

    with pytest.raises(InputDataError, match="fim não pode ser anterior"):
        load_expenses(path)


def test_rn011_fim_mes_posterior_aceito(tmp_path: Path) -> None:
    path = _write_batch(
        tmp_path,
        competence="2026-07",
        start="2026-07-01",
        end="2026-08-15",
    )

    batch = load_expenses(path)

    assert batch.period["fim"] == "2026-08-15"


def test_rn011_inicio_qualquer_dia_mes(tmp_path: Path) -> None:
    path = _write_batch(
        tmp_path,
        competence="2026-07",
        start="2026-07-15",
        end="2026-07-31",
    )

    batch = load_expenses(path)

    assert batch.period["inicio"] == "2026-07-15"
