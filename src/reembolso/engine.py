"""Calculation engine: orchestrates all rules in the spec-defined order."""

from datetime import date
from decimal import Decimal

from reembolso.category_rules import evaluate_category
from reembolso.conversion import convert_expense_to_brl
from reembolso.deadline_rules import validate_expense_deadline
from reembolso.duplicate_rules import DuplicateDetector
from reembolso.limit_rules import apply_expense_limit
from reembolso.models import (
    CalculationResult,
    ExchangeRates,
    Expense,
    ExpenseDecision,
    InputBatch,
    Policy,
)
from reembolso.receipt_rules import evaluate_receipt_requirement
from reembolso.review_rules import evaluate_manual_review
from reembolso.rounding import round_brl
from reembolso.travel_rules import identify_travel_days
from reembolso.value_rules import validate_expense_value


def _decide_expense(
    expense: Expense,
    policy: Policy,
    exchange_rates: ExchangeRates,
    cost_center: str,
    travel_days: frozenset[date],
    duplicate_detector: DuplicateDetector,
    calculation_date: date,
) -> ExpenseDecision:
    """Apply all rules to one expense in spec order. Returns the decision."""

    # Step 2a – Convert to BRL (T-024)
    conversion = convert_expense_to_brl(expense, exchange_rates)

    if conversion.rejected:
        # cotacao_indisponivel terminates here; no BRL value available.
        return ExpenseDecision(
            id=expense.id,
            status="recusada",
            reported_value=None,
            original_value=conversion.original_value,
            original_currency=conversion.original_currency,
            reimbursable_value=Decimal("0"),
            reasons=conversion.reasons,
        )

    reported_value: Decimal = conversion.reported_value  # type: ignore[assignment]

    # Step 3 – Value validation (T-006 / RN-008)
    value_eval = validate_expense_value(expense, reported_value)
    if value_eval.terminal:
        return ExpenseDecision(
            id=expense.id,
            status=value_eval.status or "recusada",
            reported_value=round_brl(reported_value),
            original_value=conversion.original_value,
            original_currency=conversion.original_currency,
            reimbursable_value=Decimal("0"),
            reasons=value_eval.reasons,
        )

    # Step 4 – Category validation (T-007 / RN-007)
    cat_eval = evaluate_category(expense, policy, cost_center)
    if cat_eval.rejected:
        return ExpenseDecision(
            id=expense.id,
            status=cat_eval.status or "recusada",
            reported_value=round_brl(reported_value),
            original_value=conversion.original_value,
            original_currency=conversion.original_currency,
            reimbursable_value=Decimal("0"),
            reasons=cat_eval.reasons,
        )

    # Attach resolved category so downstream rules share the normalised name.
    resolved_expense = Expense(
        id=expense.id,
        date=expense.date,
        category=expense.category,
        description=expense.description,
        supplier=expense.supplier,
        original_value=expense.original_value,
        original_currency=expense.original_currency,
        has_receipt=expense.has_receipt,
        normalized_category=cat_eval.normalized_category,
    )
    rule = cat_eval.rule  # never None after the rejection guard above

    # Step 5 – Duplicate detection (T-008 / RN-006)
    dup_eval = duplicate_detector.evaluate(resolved_expense)
    if dup_eval.terminal:
        return ExpenseDecision(
            id=expense.id,
            status=dup_eval.status or "recusada",
            reported_value=round_brl(reported_value),
            original_value=conversion.original_value,
            original_currency=conversion.original_currency,
            reimbursable_value=Decimal("0"),
            reasons=dup_eval.reasons,
        )

    # Step 6 – Deadline check (T-009 / RN-005)
    deadline_eval = validate_expense_deadline(resolved_expense, calculation_date)
    if deadline_eval.terminal:
        return ExpenseDecision(
            id=expense.id,
            status=deadline_eval.status or "recusada",
            reported_value=round_brl(reported_value),
            original_value=conversion.original_value,
            original_currency=conversion.original_currency,
            reimbursable_value=Decimal("0"),
            reasons=deadline_eval.reasons,
        )

    # Step 7 – Receipt requirement (T-010 / RN-003)
    receipt_eval = evaluate_receipt_requirement(
        resolved_expense, reported_value, policy
    )
    if receipt_eval.terminal:
        return ExpenseDecision(
            id=expense.id,
            status=receipt_eval.status or "recusada",
            reported_value=round_brl(reported_value),
            original_value=conversion.original_value,
            original_currency=conversion.original_currency,
            reimbursable_value=Decimal("0"),
            reasons=receipt_eval.reasons,
        )

    # Step 8 – Manual review / zero-limit (T-012 / RN-004, RN-012)
    assert rule is not None
    review_eval = evaluate_manual_review(resolved_expense, rule, travel_days)
    if review_eval.terminal:
        return ExpenseDecision(
            id=expense.id,
            status=review_eval.status or "revisao_manual",
            reported_value=round_brl(reported_value),
            original_value=conversion.original_value,
            original_currency=conversion.original_currency,
            reimbursable_value=Decimal("0"),
            reasons=review_eval.reasons,
        )

    # Step 9 – Apply limits (T-013 / RN-001, RN-002, RN-004)
    limit_eval = apply_expense_limit(
        resolved_expense,
        reported_value,
        policy,
        cost_center,
        travel_days,
    )

    reimbursable_rounded = round_brl(limit_eval.reimbursable_value)
    return ExpenseDecision(
        id=expense.id,
        status=limit_eval.status,
        reported_value=round_brl(reported_value),
        original_value=conversion.original_value,
        original_currency=conversion.original_currency,
        reimbursable_value=reimbursable_rounded,
        reasons=limit_eval.reasons,
    )


def calculate(
    batch: InputBatch,
    policy: Policy,
    exchange_rates: ExchangeRates,
    calculation_date: date,
) -> CalculationResult:
    """Run the full reimbursement calculation for one expense batch.

    Steps follow the application order in the spec:
      2  – Identify travel days across the whole batch.
      3–9 – Evaluate each expense item in sequence.
      10  – Totals are summed from already-rounded per-expense values.
    """

    cost_center: str = batch.collaborator.get("centro_custo", "")

    # Step 2 – Batch pre-analysis: travel days (T-011 / RN-004)
    travel_days = identify_travel_days(batch.expenses)

    duplicate_detector = DuplicateDetector()
    decisions: list[ExpenseDecision] = []

    for expense in batch.expenses:
        decision = _decide_expense(
            expense,
            policy,
            exchange_rates,
            cost_center,
            travel_days,
            duplicate_detector,
            calculation_date,
        )
        decisions.append(decision)

    # Step 10 – Totals (T-014 / RN-009); values are already rounded per item.
    reimbursable_total = sum(
        (
            d.reimbursable_value
            for d in decisions
            if d.status in {"reembolsada", "reembolsada_parcialmente"}
        ),
        Decimal("0"),
    )
    review_total = sum(
        (
            d.reported_value
            for d in decisions
            if d.status == "revisao_manual" and d.reported_value is not None
        ),
        Decimal("0"),
    )

    return CalculationResult(
        schema_version="2.0",
        calculation_date=calculation_date,
        currency="BRL",
        collaborator=batch.collaborator,
        period=batch.period,
        expenses=tuple(decisions),
        reimbursable_total=reimbursable_total,
        review_total=review_total,
    )
