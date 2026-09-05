import asyncio
from datetime import date
from decimal import Decimal
from uuid import UUID

from api.models import ExceptionRecord, LedgerLine, Match, ReconciliationRun
from api.reconciliation import run_reconciliation
from packages.engine.reconciliation import MatchStatus, ReasonCode


class Transaction:
    async def __aenter__(self) -> "Transaction":
        return self

    async def __aexit__(self, *args: object) -> None:
        return None


class ScalarResult:
    def __init__(self, values: list[object]) -> None:
        self.values = values

    def all(self) -> list[object]:
        return self.values


class FakeSession:
    def __init__(self, rows: list[LedgerLine], batches: list[list[LedgerLine]] | None = None) -> None:
        self.rows = {row.id: row for row in rows}
        self.batches = batches
        self.added: list[object] = []
        self.run: ReconciliationRun | None = None
        self.begin_calls = 0
        self.scalar_calls = 0

    def begin(self) -> Transaction:
        self.begin_calls += 1
        return Transaction()

    def in_transaction(self) -> bool:
        return False

    async def get(self, model: type[object], record_id: UUID) -> object | None:
        if model is ReconciliationRun:
            return self.run
        return self.rows.get(record_id)

    async def flush(self) -> None:
        return None

    def add(self, item: object) -> None:
        self.added.append(item)
        if isinstance(item, ReconciliationRun):
            self.run = item

    async def scalars(self, statement: object) -> ScalarResult:
        self.scalar_calls += 1
        if self.scalar_calls <= 2:
            if self.batches is not None:
                return ScalarResult(self.batches[self.scalar_calls - 1])
            return ScalarResult([list(self.rows.values())[self.scalar_calls - 1]])
        if self.run is None:
            return ScalarResult([])
        if "matches" in str(statement):
            return ScalarResult([item for item in self.added if isinstance(item, Match)])
        return ScalarResult([item for item in self.added if isinstance(item, ExceptionRecord)])


def row(record_id: UUID, ref: str, amount: str, day: int) -> LedgerLine:
    return LedgerLine(
        id=record_id, source="razorpay", external_ref=ref, amount=Decimal(amount),
        currency="INR", txn_date=date(2026, 1, day), description=ref, raw_payload={"id": ref},
    )


def custom_row(record_id: UUID, ref: str | None, amount: str, day: int, description: str, currency: str = "INR") -> LedgerLine:
    result = row(record_id, ref or "", amount, day)
    result.external_ref = ref
    result.description = description
    result.currency = currency
    return result


LEFT_ID = UUID("00000000-0000-0000-0000-000000000001")
RIGHT_ID = UUID("00000000-0000-0000-0000-000000000002")


def test_reconciliation_persists_match_and_done_summary() -> None:
    session = FakeSession([row(LEFT_ID, "shared", "100.00", 1), row(RIGHT_ID, "shared", "100.00", 1)])
    summary = asyncio.run(run_reconciliation(session, [LEFT_ID], [RIGHT_ID]))
    assert summary.status == "done"
    assert summary.matched_count == 1
    assert summary.review_count == 0
    assert summary.exception_count == 0
    assert summary.match_rate == Decimal("100.00")
    assert summary.match_rate_dollar == Decimal("100.00")
    assert summary.tier_breakdown == {1: 1}
    assert any(isinstance(item, Match) and item.status == MatchStatus.AUTO_MATCHED.value for item in session.added)


def test_empty_dataset_is_done_with_zero_rate() -> None:
    session = FakeSession([])
    summary = asyncio.run(run_reconciliation(session, [], []))
    assert summary.status == "done"
    assert summary.matched_count == 0
    assert summary.unmatched_count == 0
    assert summary.match_rate == Decimal("0.00")


def test_rerunning_same_records_reuses_done_run_without_duplicate_results() -> None:
    session = FakeSession([row(LEFT_ID, "shared", "100.00", 1), row(RIGHT_ID, "shared", "100.00", 1)])
    first = asyncio.run(run_reconciliation(session, [LEFT_ID], [RIGHT_ID]))
    added_count = len(session.added)
    second = asyncio.run(run_reconciliation(session, [LEFT_ID], [RIGHT_ID]))
    assert first.run_id == second.run_id
    assert len(session.added) == added_count


def test_tier_two_and_tier_three_review_results_are_persisted() -> None:
    left = custom_row(LEFT_ID, "tier-two", "100.00", 1, "payment")
    right = custom_row(RIGHT_ID, "tier-two", "101.00", 2, "payment")
    session = FakeSession([left, right])
    summary = asyncio.run(run_reconciliation(session, [LEFT_ID], [RIGHT_ID]))
    assert summary.tier_breakdown == {2: 1}
    assert summary.match_rate_dollar == Decimal("100.00")

    left = custom_row(LEFT_ID, None, "100.00", 1, "Acme payment settlement")
    right = custom_row(RIGHT_ID, "other", "100.00", 1, "Acme payment settlement pending")
    session = FakeSession([left, right])
    summary = asyncio.run(run_reconciliation(session, [LEFT_ID], [RIGHT_ID]))
    assert summary.tier_breakdown == {3: 1}
    assert summary.review_count == 1
    assert any(isinstance(item, Match) and item.status == MatchStatus.MATCHED_NEEDS_REVIEW.value for item in session.added)


def test_exceptions_duplicate_currency_and_one_to_one_are_persisted() -> None:
    left = custom_row(LEFT_ID, "bad-amount", "100.00", 1, "amount")
    right = custom_row(RIGHT_ID, "bad-amount", "103.00", 1, "amount")
    session = FakeSession([left, right])
    summary = asyncio.run(run_reconciliation(session, [LEFT_ID], [RIGHT_ID]))
    assert summary.exception_count == 1
    assert summary.reason_code_breakdown == {ReasonCode.AMOUNT_VARIANCE_EXCEEDS_TOLERANCE.value: 1}
    assert any(isinstance(item, ExceptionRecord) for item in session.added)

    left = custom_row(LEFT_ID, "currency", "100.00", 1, "currency", "USD")
    right = custom_row(RIGHT_ID, "currency", "100.00", 1, "currency", "EUR")
    session = FakeSession([left, right])
    summary = asyncio.run(run_reconciliation(session, [LEFT_ID], [RIGHT_ID]))
    assert summary.reason_code_breakdown == {ReasonCode.CURRENCY_FX_MISMATCH.value: 1}

    duplicate_left = custom_row(LEFT_ID, "duplicate", "100.00", 1, "duplicate")
    right_one = custom_row(RIGHT_ID, "duplicate", "100.00", 1, "duplicate")
    right_two = custom_row(UUID("00000000-0000-0000-0000-000000000003"), "duplicate", "100.00", 1, "duplicate")
    session = FakeSession([duplicate_left, right_one, right_two], [[duplicate_left], [right_one, right_two]])
    summary = asyncio.run(run_reconciliation(session, [LEFT_ID], [RIGHT_ID, right_two.id]))
    assert summary.exception_count == 1
    assert summary.reason_code_breakdown == {ReasonCode.DUPLICATE_CANDIDATE.value: 1}

    first_left = custom_row(LEFT_ID, "one", "100.00", 1, "one")
    second_left = custom_row(UUID("00000000-0000-0000-0000-000000000004"), "one", "100.00", 1, "one")
    only_right = custom_row(RIGHT_ID, "one", "100.00", 1, "one")
    session = FakeSession([first_left, second_left, only_right], [[first_left, second_left], [only_right]])
    summary = asyncio.run(run_reconciliation(session, [LEFT_ID, second_left.id], [RIGHT_ID]))
    assert summary.matched_count == 1
    assert summary.unmatched_count == 1