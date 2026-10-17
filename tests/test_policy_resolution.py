from datetime import date
from decimal import Decimal

from reembolso.models import CategoryRule, Policy


def _rule(limit: str) -> CategoryRule:
    return CategoryRule(
        limit=Decimal(limit),
        periodicity="dia",
        observation=None,
    )


def _policy() -> Policy:
    return Policy(
        version="v4",
        effective_date=date(2026, 7, 1),
        base_currency="BRL",
        default_rules={
            "alimentacao": _rule("60.00"),
            "transporte_urbano": _rule("120.00"),
        },
        cost_center_rules={
            "cc-comercial": {
                "alimentacao": _rule("90.00"),
                "representacao": _rule("250.00"),
            }
        },
        receipt_threshold=Decimal("100.00"),
        travel_increase_percent=Decimal("50"),
    )


def test_policy_centro_desconhecido_usa_padrao() -> None:
    rule = _policy().rule_for("CC-DESCONHECIDO", "alimentacao")

    assert rule is not None
    assert rule.limit == Decimal("60.00")


def test_policy_categoria_ausente_usa_padrao() -> None:
    rule = _policy().rule_for("CC-COMERCIAL", "transporte_urbano")

    assert rule is not None
    assert rule.limit == Decimal("120.00")


def test_policy_sem_regra_retorna_ausencia() -> None:
    assert _policy().rule_for("CC-COMERCIAL", "coworking") is None


def test_policy_centro_ignora_caixa_e_espacos() -> None:
    rule = _policy().rule_for("  cC-CoMeRcIaL  ", "representacao")

    assert rule is not None
    assert rule.limit == Decimal("250.00")
