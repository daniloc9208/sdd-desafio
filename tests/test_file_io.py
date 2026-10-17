import os
from pathlib import Path

import pytest

from reembolso import file_io
from reembolso.errors import PathCollisionError, ReembolsoError
from reembolso.file_io import validate_distinct_paths, write_atomic


def _four_distinct_paths(tmp_path: Path) -> list[Path]:
    return [
        tmp_path / "despesas.json",
        tmp_path / "politica.json",
        tmp_path / "cambio.json",
        tmp_path / "resultado.json",
    ]


def test_io_rejeita_caminhos_equivalentes(tmp_path: Path) -> None:
    paths = _four_distinct_paths(tmp_path)
    equivalent_output = tmp_path / "subdiretorio" / ".." / paths[0].name

    with pytest.raises(PathCollisionError, match="despesas e saida"):
        validate_distinct_paths(*paths[:3], equivalent_output)

    assert issubclass(PathCollisionError, ReembolsoError)

    paths[0].write_text("entrada", encoding="utf-8")
    os.link(paths[0], paths[3])

    with pytest.raises(PathCollisionError, match="despesas e saida"):
        validate_distinct_paths(*paths)


def test_io_rejeita_colisao_entre_qualquer_par(tmp_path: Path) -> None:
    paths = _four_distinct_paths(tmp_path)

    with pytest.raises(PathCollisionError, match="politica e cambio"):
        validate_distinct_paths(paths[0], paths[1], paths[1], paths[3])


def test_io_grava_substituicao_atomica(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    destination = tmp_path / "resultado.json"
    destination.write_text("conteudo anterior", encoding="utf-8")
    new_content = '{"resultado": "completo"}'
    real_replace = os.replace
    observed: dict[str, object] = {}

    def inspect_then_replace(source: str | Path, target: str | Path) -> None:
        temporary = Path(source)
        observed["temporary_parent"] = temporary.parent
        observed["temporary_content"] = temporary.read_text(encoding="utf-8")
        observed["destination_before_replace"] = destination.read_text(encoding="utf-8")
        real_replace(source, target)

    monkeypatch.setattr(file_io.os, "replace", inspect_then_replace)

    write_atomic(destination, new_content)

    assert observed == {
        "temporary_parent": tmp_path,
        "temporary_content": new_content,
        "destination_before_replace": "conteudo anterior",
    }
    assert destination.read_text(encoding="utf-8") == new_content
    assert list(tmp_path.glob(f".{destination.name}.*.tmp")) == []


@pytest.mark.parametrize("failure_stage", ["write", "replace"])
def test_io_remove_temporario_apos_falha(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    failure_stage: str,
) -> None:
    destination = tmp_path / "resultado.json"
    destination.write_text("conteudo preservado", encoding="utf-8")
    original_error = OSError(f"falha em {failure_stage}")

    if failure_stage == "write":

        def fail_write(_stream: object, _content: str) -> None:
            raise original_error

        monkeypatch.setattr(file_io, "_write_complete_text", fail_write)
    else:

        def fail_replace(_source: object, _target: object) -> None:
            raise original_error

        monkeypatch.setattr(file_io.os, "replace", fail_replace)

    with pytest.raises(OSError) as raised:
        write_atomic(destination, "novo conteudo")

    assert raised.value is original_error
    assert destination.read_text(encoding="utf-8") == "conteudo preservado"
    assert list(tmp_path.glob(f".{destination.name}.*.tmp")) == []


def test_io_falha_de_limpeza_nao_mascara_erro_original(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    destination = tmp_path / "resultado.json"
    original_error = OSError("falha na escrita")

    def fail_write(_stream: object, _content: str) -> None:
        raise original_error

    def fail_cleanup(_path: Path) -> None:
        raise OSError("falha na limpeza")

    monkeypatch.setattr(file_io, "_write_complete_text", fail_write)
    monkeypatch.setattr(Path, "unlink", fail_cleanup)

    with pytest.raises(OSError) as raised:
        write_atomic(destination, "novo conteudo")

    assert raised.value is original_error
