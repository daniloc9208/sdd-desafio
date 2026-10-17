"""Integration tests: core (T-017, T-018) and CLI (T-019, T-020, T-025)."""

import json
import subprocess
import sys
import tempfile
from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest

from reembolso.engine import calculate
from reembolso.exchange_rate_data import load_exchange_rates
from reembolso.input_data import load_expenses
from reembolso.models import (
    CategoryRule,
    ExchangeRates,
    Expense,
    InputBatch,
    Policy,
)
from reembolso.policy_data import load_policy
from reembolso.serializer import serialize_result

# ---------------------------------------------------------------------------
# Paths to fixture files
# ---------------------------------------------------------------------------

_FIXTURES = Path(__file__).parent.parent / "exemplos"
_EXEMPLO = _FIXTURES / "despesas-exemplo.json"
_ENVELOPE_DIR = _FIXTURES / "envelope"
_ENVELOPE_MAIN = _ENVELOPE_DIR / "despesas-envelope.json"
_ENVELOPE_CC = _ENVELOPE_DIR / "despesas-envelope-cc-desconhecido.json"
_POLICY_V4 = _ENVELOPE_DIR / "politica-v4.json"
_CAMBIO = _ENVELOPE_DIR / "cambio.json"

_CALC_DATE = date(2026, 7, 31)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _load_all(expenses_path: Path) -> tuple:
    batch = load_expenses(expenses_path)
    policy = load_policy(_POLICY_V4, _CALC_DATE)
    rates = load_exchange_rates(_CAMBIO)
    return batch, policy, rates


# ---------------------------------------------------------------------------
# T-017 — Empty batch and minimum input
# ---------------------------------------------------------------------------


def _simple_policy() -> Policy:
    return Policy(
        version="teste",
        effective_date=date(2026, 1, 1),
        base_currency="BRL",
        default_rules={
            "alimentacao": CategoryRule(
                limit=Decimal("60"), periodicity="dia", observation=None
            )
        },
        cost_center_rules={},
        receipt_threshold=Decimal("100"),
        travel_increase_percent=Decimal("50"),
    )


def _brl_rates() -> ExchangeRates:
    return ExchangeRates(base_currency="BRL", rates={})


def _batch_with(expenses: tuple) -> InputBatch:
    return InputBatch(
        collaborator={"id": "c-001", "nome": "Teste", "centro_custo": "CC-X"},
        period={"competencia": "2026-07", "inicio": "2026-07-01", "fim": "2026-07-31"},
        expenses=expenses,
    )


def test_lote_vazio_saida_valida() -> None:
    """despesas: [] produces a valid result with zero totals."""
    result = calculate(_batch_with(()), _simple_policy(), _brl_rates(), _CALC_DATE)

    assert result.expenses == ()
    assert result.reimbursable_total == Decimal("0")
    assert result.review_total == Decimal("0")

    # Serializer must accept an empty batch without error.
    output = json.loads(serialize_result(result))
    assert output["despesas"] == []
    assert output["totais"]["valor_reembolsavel"] == "0.00"
    assert output["totais"]["valor_em_revisao"] == "0.00"


def test_lote_uma_despesa_valida() -> None:
    """Single expense below limit must be fully reimbursed."""
    expense = Expense(
        id="d-001",
        date=date(2026, 7, 15),
        category="alimentacao",
        description="Almoco",
        supplier="Restaurante",
        original_value=Decimal("38.00"),
        original_currency="BRL",
        has_receipt=True,
    )
    result = calculate(
        _batch_with((expense,)), _simple_policy(), _brl_rates(), _CALC_DATE
    )

    assert len(result.expenses) == 1
    decision = result.expenses[0]
    assert decision.status == "reembolsada"
    assert decision.reimbursable_value == Decimal("38.00")
    assert result.reimbursable_total == Decimal("38.00")


# ---------------------------------------------------------------------------
# T-018 — Core integration with the complete sample batch
# ---------------------------------------------------------------------------


def test_integracao_lote_completo() -> None:
    """Run the full sample against policy-v4 and verify all 14 decisions."""
    batch, policy, rates = _load_all(_EXEMPLO)
    result = calculate(batch, policy, rates, _CALC_DATE)

    decisions = {d.id: d for d in result.expenses}
    assert len(decisions) == 14

    # d-001, d-002: alimentacao on 2026-07-03 — travel_days non-empty, date outside
    for eid in ("d-001", "d-002"):
        assert decisions[eid].status == "revisao_manual", eid

    # d-003, d-004: transporte_urbano without receipt >= 100
    for eid in ("d-003", "d-004"):
        assert decisions[eid].status == "recusada", eid
        assert any(r.code == "nota_fiscal_ausente" for r in decisions[eid].reasons), eid

    # d-005: coworking — not in policy
    assert decisions["d-005"].status == "recusada"
    assert any(r.code == "categoria_fora_politica" for r in decisions["d-005"].reasons)

    # d-006: revisao_manual (date not in travel days)
    assert decisions["d-006"].status == "revisao_manual"

    # d-007: duplicate of d-006
    assert decisions["d-007"].status == "recusada"
    assert any(r.code == "duplicata" for r in decisions["d-007"].reasons)

    # d-008: prazo_excedido (2026-04-15 → 107 days)
    assert decisions["d-008"].status == "recusada"
    assert any(r.code == "prazo_excedido" for r in decisions["d-008"].reasons)

    # d-009: valor negativo
    assert decisions["d-009"].status == "recusada"
    assert any(
        r.code == "valor_negativo_fora_escopo" for r in decisions["d-009"].reasons
    )

    # d-010: limite zero (hospedagem CC-ENG-PLATAFORMA), still generates travel day
    assert decisions["d-010"].status == "recusada"
    assert any(
        r.code == "limite_zero_nao_reembolsavel" for r in decisions["d-010"].reasons
    )

    # d-011: alimentacao on 2026-07-15 (travel day generated by d-010)
    d011 = decisions["d-011"]
    assert d011.status == "reembolsada"
    assert d011.reimbursable_value == Decimal("33.33")
    assert any(r.code == "limite_viagem_aplicado" for r in d011.reasons)
    assert any(r.code == "dentro_do_limite" for r in d011.reasons)

    # d-012: alimentacao on 2026-07-18 — not in travel days
    assert decisions["d-012"].status == "revisao_manual"

    # d-013: hospedagem without receipt >= 100; still generates travel day 2026-07-23
    assert decisions["d-013"].status == "recusada"
    assert any(r.code == "nota_fiscal_ausente" for r in decisions["d-013"].reasons)

    # d-014: ALIMENTACAO (uppercase) on 2026-07-31 — not a travel day
    assert decisions["d-014"].status == "revisao_manual"

    # Totals
    assert result.reimbursable_total == Decimal("33.33")
    assert result.review_total == Decimal("273.60")


# ---------------------------------------------------------------------------
# T-019 — CLI integration via subprocess
# ---------------------------------------------------------------------------


def test_cli_integracao_subprocess() -> None:
    """Invoke the CLI via subprocess and verify output contract fields."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "resultado.json"
        cmd = [
            sys.executable,
            "-m",
            "reembolso",
            "calcular",
            "--input",
            str(_EXEMPLO),
            "--output",
            str(output_path),
            "--policy",
            str(_POLICY_V4),
            "--exchange-rates",
            str(_CAMBIO),
        ]
        proc = subprocess.run(cmd, capture_output=True, text=True)
        assert proc.returncode == 0, proc.stderr

        with output_path.open("r", encoding="utf-8") as fh:
            output = json.load(fh)

        assert output["versao_schema"] == "2.0"
        assert output["moeda"] == "BRL"
        # data_calculo must be a valid ISO date string
        parsed_date = date.fromisoformat(output["data_calculo"])
        assert isinstance(parsed_date, date)
        assert isinstance(output["despesas"], list)
        assert "totais" in output


def test_cli_exige_arquivos_policy_e_exchange_rates() -> None:
    """CLI returns non-zero when required arguments are missing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "resultado.json"

        # Missing --policy
        proc = subprocess.run(
            [
                sys.executable,
                "-m",
                "reembolso",
                "calcular",
                "--input",
                str(_EXEMPLO),
                "--output",
                str(output_path),
                "--exchange-rates",
                str(_CAMBIO),
            ],
            capture_output=True,
            text=True,
        )
        assert proc.returncode != 0

        # Missing --exchange-rates
        proc = subprocess.run(
            [
                sys.executable,
                "-m",
                "reembolso",
                "calcular",
                "--input",
                str(_EXEMPLO),
                "--output",
                str(output_path),
                "--policy",
                str(_POLICY_V4),
            ],
            capture_output=True,
            text=True,
        )
        assert proc.returncode != 0


def test_cli_codigo_zero_com_recusas() -> None:
    """Structurally valid input with rejected expenses returns exit code 0."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "resultado.json"
        cmd = [
            sys.executable,
            "-m",
            "reembolso",
            "calcular",
            "--input",
            str(_EXEMPLO),
            "--output",
            str(output_path),
            "--policy",
            str(_POLICY_V4),
            "--exchange-rates",
            str(_CAMBIO),
        ]
        proc = subprocess.run(cmd, capture_output=True, text=True)
        assert proc.returncode == 0


def test_cli_codigo_nonzero_entrada_invalida() -> None:
    """Non-existent input file produces a non-zero exit code."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "resultado.json"
        proc = subprocess.run(
            [
                sys.executable,
                "-m",
                "reembolso",
                "calcular",
                "--input",
                str(Path(tmpdir) / "nao-existe.json"),
                "--output",
                str(output_path),
                "--policy",
                str(_POLICY_V4),
                "--exchange-rates",
                str(_CAMBIO),
            ],
            capture_output=True,
            text=True,
        )
        assert proc.returncode != 0


# ---------------------------------------------------------------------------
# T-020 — Output preservation on I/O failure
# ---------------------------------------------------------------------------


def test_io_preserva_saida_em_falha_gravacao() -> None:
    """Existing output is preserved when write_atomic fails mid-write."""
    import unittest.mock as mock

    from reembolso.file_io import write_atomic

    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "resultado.json"
        original_content = '{"original": true}'
        output_path.write_text(original_content, encoding="utf-8")

        # Simulate failure during os.replace
        with mock.patch("reembolso.file_io.os.replace", side_effect=OSError("falha")):
            with pytest.raises(OSError):
                write_atomic(output_path, '{"novo": true}')

        assert output_path.read_text(encoding="utf-8") == original_content


def test_io_preserva_saida_arquivo_entrada_ausente() -> None:
    """Missing input file leaves any pre-existing output untouched."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "resultado.json"
        original_content = '{"original": true}'
        output_path.write_text(original_content, encoding="utf-8")

        cmd = [
            sys.executable,
            "-m",
            "reembolso",
            "calcular",
            "--input",
            str(Path(tmpdir) / "nao-existe.json"),
            "--output",
            str(output_path),
            "--policy",
            str(_POLICY_V4),
            "--exchange-rates",
            str(_CAMBIO),
        ]
        proc = subprocess.run(cmd, capture_output=True, text=True)
        assert proc.returncode != 0
        assert output_path.read_text(encoding="utf-8") == original_content


def test_io_preserva_saida_configuracao_invalida() -> None:
    """Invalid policy leaves pre-existing output untouched."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "resultado.json"
        invalid_policy = Path(tmpdir) / "politica-invalida.json"
        invalid_policy.write_text('{"versao": "x", "invalido": true}', encoding="utf-8")
        original_content = '{"original": true}'
        output_path.write_text(original_content, encoding="utf-8")

        cmd = [
            sys.executable,
            "-m",
            "reembolso",
            "calcular",
            "--input",
            str(_EXEMPLO),
            "--output",
            str(output_path),
            "--policy",
            str(invalid_policy),
            "--exchange-rates",
            str(_CAMBIO),
        ]
        proc = subprocess.run(cmd, capture_output=True, text=True)
        assert proc.returncode != 0
        assert output_path.read_text(encoding="utf-8") == original_content


# ---------------------------------------------------------------------------
# T-025 — Envelope end-to-end (both fixtures)
# ---------------------------------------------------------------------------


def test_envelope_despesas_principais() -> None:
    """Validate all 10 decisions for despesas-envelope.json (CC-COMERCIAL)."""
    batch, policy, rates = _load_all(_ENVELOPE_MAIN)
    result = calculate(batch, policy, rates, _CALC_DATE)

    decisions = {d.id: d for d in result.expenses}
    assert len(decisions) == 10

    # e-001: representacao 340 BRL — date not in travel_days → revisao_manual
    assert decisions["e-001"].status == "revisao_manual"
    assert decisions["e-001"].reported_value == Decimal("340.00")

    # e-002: alimentacao 22 EUR × 5.93 = 130.46 BRL → revisao_manual
    assert decisions["e-002"].status == "revisao_manual"
    assert decisions["e-002"].reported_value == Decimal("130.46")

    # e-003: alimentacao 14.50 EUR × 5.88 = 85.26 BRL → revisao_manual
    assert decisions["e-003"].status == "revisao_manual"
    assert decisions["e-003"].reported_value == Decimal("85.26")

    # e-004: alimentacao 30 EUR × 5.96 = 178.80 BRL → revisao_manual
    assert decisions["e-004"].status == "revisao_manual"
    assert decisions["e-004"].reported_value == Decimal("178.80")

    # e-005: transporte_urbano 40 USD × 5.50 = 220 BRL, no receipt → recusada
    assert decisions["e-005"].status == "recusada"
    assert any(r.code == "nota_fiscal_ausente" for r in decisions["e-005"].reasons)
    assert decisions["e-005"].reported_value == Decimal("220.00")

    # e-006: representacao 55 GBP — no GBP rate → cotacao_indisponivel
    assert decisions["e-006"].status == "recusada"
    assert any(r.code == "cotacao_indisponivel" for r in decisions["e-006"].reasons)
    assert decisions["e-006"].reported_value is None

    # e-007: hospedagem 1200 BRL, limit=400 → revisao_manual
    assert decisions["e-007"].status == "revisao_manual"
    assert decisions["e-007"].reported_value == Decimal("1200.00")

    # e-008: alimentacao 95 BRL on 2026-07-23 (travel day from e-007) → reembolsada
    e008 = decisions["e-008"]
    assert e008.status == "reembolsada"
    assert e008.reimbursable_value == Decimal("95.00")
    assert any(r.code == "limite_viagem_aplicado" for r in e008.reasons)
    assert any(r.code == "dentro_do_limite" for r in e008.reasons)

    # e-009: coworking — not in policy
    assert decisions["e-009"].status == "recusada"
    assert any(r.code == "categoria_fora_politica" for r in decisions["e-009"].reasons)

    # e-010: alimentacao 88 BRL on 2026-07-27 — not in travel days
    assert decisions["e-010"].status == "revisao_manual"
    assert decisions["e-010"].reported_value == Decimal("88.00")

    # Totals
    assert result.reimbursable_total == Decimal("95.00")
    assert result.review_total == Decimal("2022.52")


def test_envelope_centro_desconhecido() -> None:
    """Validate all 4 decisions for despesas-envelope-cc-desconhecido.json."""
    batch, policy, rates = _load_all(_ENVELOPE_CC)
    result = calculate(batch, policy, rates, _CALC_DATE)

    decisions = {d.id: d for d in result.expenses}
    assert len(decisions) == 4

    # f-001: alimentacao 58 BRL on 2026-07-16 — travel_days={2026-07-18}, not in
    assert decisions["f-001"].status == "revisao_manual"
    assert decisions["f-001"].reported_value == Decimal("58.00")

    # f-002: hospedagem 310 BRL — revisao_manual
    assert decisions["f-002"].status == "revisao_manual"
    assert decisions["f-002"].reported_value == Decimal("310.00")

    # f-003: representacao — not in default policy → recusada
    assert decisions["f-003"].status == "recusada"
    assert any(r.code == "categoria_fora_politica" for r in decisions["f-003"].reasons)

    # f-004: transporte_urbano 12 USD × 5.48 = 65.76 BRL on 2026-07-21
    assert decisions["f-004"].status == "revisao_manual"
    assert decisions["f-004"].reported_value == Decimal("65.76")

    # Totals
    assert result.reimbursable_total == Decimal("0.00")
    assert result.review_total == Decimal("433.76")


def test_valor_informado_convertido_em_despesa_recusada() -> None:
    """A rejected expense (by category) still reports its BRL equivalent."""
    batch, policy, rates = _load_all(_ENVELOPE_CC)
    result = calculate(batch, policy, rates, _CALC_DATE)
    decisions = {d.id: d for d in result.expenses}

    # f-003 is rejected by categoria_fora_politica but has a BRL value (190 BRL)
    f003 = decisions["f-003"]
    assert f003.status == "recusada"
    assert f003.reported_value == Decimal("190.00")
