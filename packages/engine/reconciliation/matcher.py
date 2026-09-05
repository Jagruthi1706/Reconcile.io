from dataclasses import dataclass
from decimal import Decimal
from typing import Sequence

from packages.engine.canonical import CanonicalLedgerRecord
from packages.engine.reconciliation.models import (
    ExceptionDecision,
    MatchDecision,
    MatchStatus,
    ReconciliationResult,
)
from packages.engine.reconciliation.reason_codes import ReasonCode
from packages.engine.reconciliation.scoring import (
    absolute_amount_variance,
    date_distance,
    description_similarity,
    tier_three_confidence,
    tier_two_confidence,
    within_amount_tolerance,
    within_date_window,
)


@dataclass(frozen=True, slots=True)
class MatcherConfig:
    amount_tolerance_pct: Decimal = Decimal("1.5")
    date_window_days: int = 5
    auto_accept_confidence: Decimal = Decimal("0.90")
    tier_three_similarity_threshold: Decimal = Decimal("0.50")


def reconcile(
    left_records: Sequence[CanonicalLedgerRecord],
    right_records: Sequence[CanonicalLedgerRecord],
    config: MatcherConfig | None = None,
) -> ReconciliationResult:
    """Reconcile two normalized record collections with deterministic tiers.

    The inputs are already canonicalized. This function has no provider, API,
    persistence, or LLM dependencies and never fabricates a match to consume a
    candidate. Each right-side record can be used at most once.
    """
    settings = config or MatcherConfig()
    used_right_ids: set = set()
    matches: list[MatchDecision] = []
    exceptions: list[ExceptionDecision] = []

    for left in left_records:
        available = [record for record in right_records if record.id not in used_right_ids]
        candidates = _find_candidates(left, available, settings)

        if len(candidates) > 1:
            exceptions.append(ExceptionDecision(left.id, ReasonCode.DUPLICATE_CANDIDATE, "Multiple deterministic candidates matched the record."))
            continue
        if len(candidates) == 1:
            candidate, tier, confidence = candidates[0]
            used_right_ids.add(candidate.id)
            status = (
                MatchStatus.AUTO_MATCHED
                if confidence >= settings.auto_accept_confidence
                else MatchStatus.MATCHED_NEEDS_REVIEW
            )
            matches.append(MatchDecision(left.id, candidate.id, tier, confidence, absolute_amount_variance(left.amount, candidate.amount), status))
            continue

        if _find_candidates(left, right_records, settings):
            code = ReasonCode.DUPLICATE_CANDIDATE
            text = "A compatible counterpart was already consumed by another record."
        else:
            code = _classify_exception(left, right_records, settings)
            text = _exception_text(left, right_records, settings)
        exceptions.append(ExceptionDecision(left.id, code, text))

    return ReconciliationResult(tuple(matches), tuple(exceptions))


def _find_candidates(
    left: CanonicalLedgerRecord,
    right_records: Sequence[CanonicalLedgerRecord],
    config: MatcherConfig,
) -> list[tuple[CanonicalLedgerRecord, int, Decimal]]:
    tier_one: list[tuple[CanonicalLedgerRecord, int, Decimal]] = []
    tier_two: list[tuple[CanonicalLedgerRecord, int, Decimal]] = []
    tier_three: list[tuple[CanonicalLedgerRecord, int, Decimal]] = []

    for right in right_records:
        if left.currency != right.currency:
            continue
        same_reference = bool(left.external_ref and right.external_ref and left.external_ref == right.external_ref)
        exact_amount = left.amount == right.amount
        date_ok = within_date_window(left.txn_date, right.txn_date, config.date_window_days)

        if same_reference and exact_amount:
            tier_one.append((right, 1, Decimal("1.000")))
        elif same_reference and within_amount_tolerance(left.amount, right.amount, config.amount_tolerance_pct) and date_ok:
            tier_two.append((right, 2, tier_two_confidence(left.amount, right.amount, left.txn_date, right.txn_date, config.amount_tolerance_pct, config.date_window_days)))
        elif not left.external_ref and exact_amount and date_ok:
            similarity = description_similarity(left.description, right.description)
            if similarity >= config.tier_three_similarity_threshold:
                tier_three.append((right, 3, tier_three_confidence(similarity)))

    return tier_one or tier_two or tier_three


def _classify_exception(
    left: CanonicalLedgerRecord,
    right_records: Sequence[CanonicalLedgerRecord],
    config: MatcherConfig,
) -> ReasonCode:
    if _is_in_transit(left):
        return ReasonCode.IN_TRANSIT_NOT_CLEARED

    same_reference = [record for record in right_records if left.external_ref and record.external_ref == left.external_ref]
    if same_reference:
        if any(record.currency != left.currency for record in same_reference):
            return ReasonCode.CURRENCY_FX_MISMATCH
        if any(not within_amount_tolerance(left.amount, record.amount, config.amount_tolerance_pct) for record in same_reference):
            return ReasonCode.AMOUNT_VARIANCE_EXCEEDS_TOLERANCE
        if any(not within_date_window(left.txn_date, record.txn_date, config.date_window_days) for record in same_reference):
            return ReasonCode.DATE_VARIANCE_EXCEEDS_WINDOW

    comparable = [record for record in right_records if record.currency == left.currency]
    if not comparable:
        return ReasonCode.CURRENCY_FX_MISMATCH if right_records else ReasonCode.NO_COUNTERPART
    if left.external_ref:
        return ReasonCode.STALE_REFERENCE
    if any(left.amount == record.amount and not within_date_window(left.txn_date, record.txn_date, config.date_window_days) for record in comparable):
        return ReasonCode.DATE_VARIANCE_EXCEEDS_WINDOW
    return ReasonCode.NO_COUNTERPART


def _exception_text(
    left: CanonicalLedgerRecord,
    right_records: Sequence[CanonicalLedgerRecord],
    config: MatcherConfig,
) -> str:
    code = _classify_exception(left, right_records, config)
    return {
        ReasonCode.NO_COUNTERPART: "No compatible counterpart was found.",
        ReasonCode.STALE_REFERENCE: "The reference did not identify a compatible counterpart.",
        ReasonCode.AMOUNT_VARIANCE_EXCEEDS_TOLERANCE: "The reference exists, but amount variance exceeds tolerance.",
        ReasonCode.DATE_VARIANCE_EXCEEDS_WINDOW: "The amount/reference candidate falls outside the date window.",
        ReasonCode.IN_TRANSIT_NOT_CLEARED: "The record is marked in transit and has not cleared.",
        ReasonCode.CURRENCY_FX_MISMATCH: "Candidate records use a different currency without FX context.",
        ReasonCode.DUPLICATE_CANDIDATE: "Multiple candidates were found; no match was forced.",
    }[code]


def _is_in_transit(record: CanonicalLedgerRecord) -> bool:
    description = (record.description or "").lower()
    return "in transit" in description or "transit pending" in description
