"""Immutable data structures shared by the adapters and calculation core."""

import unicodedata
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import date
from decimal import Decimal


@dataclass(frozen=True)
class Expense:
    id: str
    date: date
    category: str
    description: str
    supplier: str
    original_value: Decimal
    original_currency: str
    has_receipt: bool


@dataclass(frozen=True)
class InputBatch:
    collaborator: Mapping[str, str]
    period: Mapping[str, str]
    expenses: tuple[Expense, ...]


@dataclass(frozen=True)
class CategoryRule:
    limit: Decimal
    periodicity: str
    observation: str | None

    @property
    def explicitly_non_reimbursable(self) -> bool:
        if self.observation is None:
            return False
        decomposed = unicodedata.normalize("NFKD", self.observation.casefold())
        normalized = "".join(
            character
            for character in decomposed
            if not unicodedata.combining(character)
        )
        return normalized.strip() == "nao reembolsavel"


@dataclass(frozen=True)
class Policy:
    version: str
    effective_date: date
    base_currency: str
    default_rules: Mapping[str, CategoryRule]
    cost_center_rules: Mapping[str, Mapping[str, CategoryRule]]
    receipt_threshold: Decimal
    travel_increase_percent: Decimal

    def rule_for(self, cost_center: str, category: str) -> CategoryRule | None:
        center_rules = self.cost_center_rules.get(cost_center)
        if center_rules is not None and category in center_rules:
            return center_rules[category]
        return self.default_rules.get(category)


@dataclass(frozen=True)
class ExchangeRates:
    base_currency: str
    rates: Mapping[date, Mapping[str, Decimal]]

    def rate_for(self, currency: str, expense_date: date) -> Decimal | None:
        eligible_dates = (
            rate_date
            for rate_date, rates in self.rates.items()
            if rate_date <= expense_date and currency in rates
        )
        latest_date = max(eligible_dates, default=None)
        if latest_date is None:
            return None
        return self.rates[latest_date].get(currency)


@dataclass(frozen=True)
class Reason:
    code: str
    description: str


@dataclass(frozen=True)
class ExpenseDecision:
    id: str
    status: str
    reported_value: Decimal | None
    original_value: Decimal
    original_currency: str
    reimbursable_value: Decimal
    reasons: tuple[Reason, ...]


@dataclass(frozen=True)
class CalculationResult:
    calculation_date: date
    collaborator: Mapping[str, str]
    period: Mapping[str, str]
    expenses: tuple[ExpenseDecision, ...]
    reimbursable_total: Decimal
    review_total: Decimal
