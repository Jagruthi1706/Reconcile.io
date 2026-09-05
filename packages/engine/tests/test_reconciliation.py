from datetime import date
from decimal import Decimal
from uuid import UUID

from packages.engine.canonical import CanonicalLedgerRecord
from packages.engine.reconciliation import MatcherConfig, MatchStatus, ReasonCode, reconcile


LEFT_ID = UUID("00000000-0000-0000-0000-000000000001")
RIGHT_ID = UUID("00000000-0000-0000-0000-000000000002")
RIGHT_ID_2 = UUID("00000000-0000-0000-0000-000000000003")


def record(record_id: UUID, *, ref: str | None = "REF-1", amount: str = "100.00", day: int = 1, description: str | None = "Acme invoice REF-1", currency: str = "USD") -> CanonicalLedgerRecord:
    return CanonicalLedgerRecord(record_id, "bank", Decimal(amount), currency, date(2026, 1, day), ref, description)


def test_tier_one_exact_reference_and_amount() -> None:
    result = reconcile([record(LEFT_ID)], [record(RIGHT_ID)])
    assert result.matches[0].tier == 1
    assert result.matches[0].confidence == Decimal("1.000")
    assert result.matches[0].status == MatchStatus.AUTO_MATCHED


def test_tier_one_duplicate_candidates_are_not_forced() -> None:
    result = reconcile([record(LEFT_ID)], [record(RIGHT_ID), record(RIGHT_ID_2)])
    assert not result.matches
    assert result.exceptions[0].reason_code == ReasonCode.DUPLICATE_CANDIDATE


def test_tier_two_amount_drift_within_tolerance() -> None:
    result = reconcile([record(LEFT_ID)], [record(RIGHT_ID, amount="101.00")])
    assert result.matches[0].tier == 2
    assert result.matches[0].status == MatchStatus.AUTO_MATCHED


def test_tier_two_date_window_handling() -> None:
    result = reconcile([record(LEFT_ID)], [record(RIGHT_ID, day=6, amount="101.00")])
    assert result.matches[0].tier == 2


def test_tier_two_tolerance_rejection() -> None:
    result = reconcile([record(LEFT_ID)], [record(RIGHT_ID, amount="103.00")])
    assert result.exceptions[0].reason_code == ReasonCode.AMOUNT_VARIANCE_EXCEEDS_TOLERANCE


def test_tier_three_description_similarity() -> None:
    left = record(LEFT_ID, ref=None, description="Acme invoice settlement")
    right = record(RIGHT_ID, ref="OTHER", description="Acme invoice settlement")
    result = reconcile([left], [right])
    assert result.matches[0].tier == 3


def test_tier_three_date_rejection() -> None:
    left = record(LEFT_ID, ref=None, description="Acme invoice settlement")
    right = record(RIGHT_ID, ref="OTHER", day=10, description="Acme invoice settlement")
    result = reconcile([left], [right])
    assert result.exceptions[0].reason_code == ReasonCode.DATE_VARIANCE_EXCEEDS_WINDOW


def test_missing_bank_reference_can_match_by_tier_three() -> None:
    result = reconcile([record(LEFT_ID, ref=None, description="Acme invoice settlement")], [record(RIGHT_ID, description="Acme invoice settlement")])
    assert result.matches[0].tier == 3


def test_missing_gl_counterpart() -> None:
    result = reconcile([record(LEFT_ID)], [])
    assert result.exceptions[0].reason_code == ReasonCode.NO_COUNTERPART


def test_in_transit_record() -> None:
    result = reconcile([record(LEFT_ID, description="Payment in transit")], [])
    assert result.exceptions[0].reason_code == ReasonCode.IN_TRANSIT_NOT_CLEARED


def test_currency_mismatch() -> None:
    result = reconcile([record(LEFT_ID, currency="USD")], [record(RIGHT_ID, currency="EUR")])
    assert result.exceptions[0].reason_code == ReasonCode.CURRENCY_FX_MISMATCH


def test_duplicate_candidate_behavior() -> None:
    left_records = [record(LEFT_ID), record(RIGHT_ID_2, ref="REF-2", amount="200.00")]
    right_records = [record(RIGHT_ID), record(UUID("00000000-0000-0000-0000-000000000004"), ref="REF-2", amount="200.00")]
    result = reconcile(left_records, right_records)
    assert len(result.matches) == 2
    assert len({match.right_id for match in result.matches}) == 2


def test_confidence_threshold_behavior() -> None:
    config = MatcherConfig(auto_accept_confidence=Decimal("1.001"))
    result = reconcile([record(LEFT_ID)], [record(RIGHT_ID)], config)
    assert result.matches[0].status == MatchStatus.MATCHED_NEEDS_REVIEW


def test_decimal_monetary_comparison() -> None:
    result = reconcile([record(LEFT_ID, amount="100.10")], [record(RIGHT_ID, amount="102.00")])
    assert result.exceptions[0].reason_code == ReasonCode.AMOUNT_VARIANCE_EXCEEDS_TOLERANCE


def test_one_to_one_matching_protection() -> None:
    left_records = [record(LEFT_ID), record(RIGHT_ID_2, ref="REF-1")]
    result = reconcile(left_records, [record(UUID("00000000-0000-0000-0000-000000000004"))])
    assert len(result.matches) == 1
    assert len(result.exceptions) == 1
    assert result.exceptions[0].reason_code == ReasonCode.DUPLICATE_CANDIDATE
