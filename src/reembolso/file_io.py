"""File-system adapter for path validation and atomic result publication."""

import os
import tempfile
from collections.abc import Sequence
from contextlib import suppress
from os import PathLike
from pathlib import Path
from typing import TextIO

from reembolso.errors import PathCollisionError

PathValue = str | PathLike[str]


def _normalized_resolved_path(path: PathValue) -> str:
    resolved = Path(path).resolve(strict=False)
    return os.path.normcase(os.path.normpath(os.fspath(resolved)))


def _existing_paths_are_same(left: Path, right: Path) -> bool:
    return left.exists() and right.exists() and os.path.samefile(left, right)


def validate_distinct_paths(
    input_path: PathValue,
    policy_path: PathValue,
    exchange_rates_path: PathValue,
    output_path: PathValue,
) -> None:
    """Ensure that the four execution paths identify distinct files."""
    named_paths: Sequence[tuple[str, Path]] = (
        ("despesas", Path(input_path)),
        ("politica", Path(policy_path)),
        ("cambio", Path(exchange_rates_path)),
        ("saida", Path(output_path)),
    )
    normalized = {name: _normalized_resolved_path(path) for name, path in named_paths}

    for index, (left_name, left_path) in enumerate(named_paths):
        for right_name, right_path in named_paths[index + 1 :]:
            same_resolved_path = normalized[left_name] == normalized[right_name]
            same_existing_file = _existing_paths_are_same(left_path, right_path)
            if same_resolved_path or same_existing_file:
                raise PathCollisionError(
                    f"os caminhos de {left_name} e {right_name} "
                    "identificam o mesmo arquivo"
                )


def _write_complete_text(stream: TextIO, content: str) -> None:
    written = stream.write(content)
    if written != len(content):
        raise OSError("não foi possível escrever o resultado completo")


def write_atomic(output_path: PathValue, content: str) -> None:
    """Write text as UTF-8 and atomically replace the destination on success."""
    destination = Path(output_path)
    temporary_path: Path | None = None

    try:
        descriptor, temporary_name = tempfile.mkstemp(
            dir=destination.parent,
            prefix=f".{destination.name}.",
            suffix=".tmp",
        )
        temporary_path = Path(temporary_name)

        try:
            stream = os.fdopen(descriptor, "w", encoding="utf-8", newline="")
        except BaseException:
            with suppress(OSError):
                os.close(descriptor)
            raise

        with stream:
            _write_complete_text(stream, content)

        os.replace(temporary_path, destination)
        temporary_path = None
    finally:
        if temporary_path is not None:
            try:
                temporary_path.unlink()
            except FileNotFoundError:
                pass
            except OSError:
                # Cleanup is best-effort and must not hide the original failure.
                pass
