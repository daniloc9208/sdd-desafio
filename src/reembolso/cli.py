"""Interface de linha de comando do motor de reembolso."""

import argparse
from collections.abc import Sequence


def build_parser() -> argparse.ArgumentParser:
    """Cria o parser da CLI pública."""
    parser = argparse.ArgumentParser(
        prog="reembolso",
        description="Motor de cálculo de reembolso de despesas corporativas.",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Executa a CLI."""
    build_parser().parse_args(argv)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
