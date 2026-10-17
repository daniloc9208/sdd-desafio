"""Interface de linha de comando do motor de reembolso."""

import argparse
import sys
from collections.abc import Sequence
from datetime import date
from pathlib import Path

from reembolso.engine import calculate
from reembolso.errors import PathCollisionError, ReembolsoError
from reembolso.exchange_rate_data import load_exchange_rates
from reembolso.file_io import validate_distinct_paths, write_atomic
from reembolso.input_data import load_expenses
from reembolso.policy_data import load_policy
from reembolso.serializer import serialize_result


def build_parser() -> argparse.ArgumentParser:
    """Cria o parser da CLI pública."""
    parser = argparse.ArgumentParser(
        prog="reembolso",
        description="Motor de cálculo de reembolso de despesas corporativas.",
    )
    subparsers = parser.add_subparsers(dest="command")

    calcular = subparsers.add_parser(
        "calcular",
        help="Calcula o reembolso a partir de um arquivo de despesas.",
    )
    calcular.add_argument(
        "--input",
        required=True,
        metavar="DESPESAS",
        help="Caminho para o arquivo JSON de despesas.",
    )
    calcular.add_argument(
        "--output",
        required=True,
        metavar="RESULTADO",
        help="Caminho para o arquivo JSON de saída.",
    )
    calcular.add_argument(
        "--policy",
        required=True,
        metavar="POLITICA",
        help="Caminho para o arquivo JSON de política.",
    )
    calcular.add_argument(
        "--exchange-rates",
        required=True,
        metavar="CAMBIO",
        dest="exchange_rates",
        help="Caminho para o arquivo JSON de cotações.",
    )
    return parser


def _run_calcular(
    input_path: Path,
    output_path: Path,
    policy_path: Path,
    exchange_rates_path: Path,
    *,
    calculation_date: date | None = None,
) -> int:
    """Execute the calcular subcommand. Returns the exit code."""
    try:
        validate_distinct_paths(
            input_path, policy_path, exchange_rates_path, output_path
        )
    except PathCollisionError as error:
        print(f"Erro: {error}", file=sys.stderr)
        return 1

    # Capture calculation date exactly once (step 2 of spec, FURO-017).
    if calculation_date is None:
        calculation_date = date.today()

    try:
        batch = load_expenses(input_path)
        policy = load_policy(policy_path, calculation_date)
        exchange_rates = load_exchange_rates(exchange_rates_path)
    except ReembolsoError as error:
        print(f"Erro: {error}", file=sys.stderr)
        return 1

    result = calculate(batch, policy, exchange_rates, calculation_date)
    json_output = serialize_result(result)

    try:
        write_atomic(output_path, json_output)
    except OSError as error:
        print(f"Erro ao gravar resultado: {error}", file=sys.stderr)
        return 1

    return 0


def main(argv: Sequence[str] | None = None) -> int:
    """Executa a CLI."""
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "calcular":
        return _run_calcular(
            input_path=Path(args.input),
            output_path=Path(args.output),
            policy_path=Path(args.policy),
            exchange_rates_path=Path(args.exchange_rates),
        )

    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
