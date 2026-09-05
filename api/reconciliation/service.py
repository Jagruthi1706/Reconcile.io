"""Orchestrate persisted records through the provider-neutral engine."""

from collections import Counter
from contextlib import asynccontextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal
from uuid import UUID, uuid5

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.ingestion import canonical_from_ledger_line
from api.models import ExceptionRecord, LedgerLine, Match, ReconciliationRun
from packages.engine.reconciliation import MatchStatus, reconcile

_RUN_NAMESPACE = UUID("7b2e26d5-bf17-4a27-9ebc-2d0d70c0e7b4")


@dataclass(frozen=True, slots=True)
class ReconciliationSummary:
    run_id: UUID
    status: str
    total_left_records: int
    total_right_records: int
    matched_count: int
    review_count: int
    exception_count: int
    unmatched_count: int
    match_rate: Decimal
    match_rate_dollar: Decimal
    tier_breakdown: dict[int, int]
    reason_code_breakdown: dict[str, int]


async def run_reconciliation(
    session: AsyncSession,
    left_ids: list[UUID] | tuple[UUID, ...],
    right_ids: list[UUID] | tuple[UUID, ...],
) -> ReconciliationSummary:
    """Run and persist one deterministic reconciliation for explicit record sets."""
    left_key = ",".join(sorted(str(record_id) for record_id in set(left_ids)))
    right_key = ",".join(sorted(str(record_id) for record_id in set(right_ids)))
    run_id = uuid5(_RUN_NAMESPACE, f"left:{left_key}|right:{right_key}")
    async with _transaction_scope(session):
        existing = await session.get(ReconciliationRun, run_id)
        if existing is not None and existing.status == "done":
            return await _summary_for_run(session, existing, len(left_ids), len(right_ids))

        run = existing or ReconciliationRun(id=run_id, status="running", triggered_by="manual")
        if existing is None:
            session.add(run)
            await session.flush()

        left_rows = await _load_rows(session, left_ids)
        right_rows = await _load_rows(session, right_ids)
        left_records = tuple(canonical_from_ledger_line(row) for row in left_rows)
        right_records = tuple(canonical_from_ledger_line(row) for row in right_rows)
        result = reconcile(left_records, right_records)

        for match in result.matches:
            session.add(Match(
                run_id=run.id, line_a_id=match.left_id, line_b_id=match.right_id,
                tier=match.tier, confidence=match.confidence, variance=match.variance,
                status=match.status.value,
            ))
        for exception in result.exceptions:
            session.add(ExceptionRecord(
                run_id=run.id, line_id=exception.record_id,
                reason_code=exception.reason_code.value, reason_text=exception.reason_text,
            ))

        run.status = "done"
        run.finished_at = datetime.now(timezone.utc)
        run.records_processed = len(left_records) + len(right_records)
        run.match_rate_count = _match_rate(len(result.matches), len(left_records))
        run.match_rate_dollar = _dollar_match_rate(left_records, result.matches)
        run.avg_settlement_lag = await _settlement_lag(session, result.matches)
        await session.flush()
        return _summary_from_result(run, result, len(left_records), len(right_records))


@asynccontextmanager
async def _transaction_scope(session: AsyncSession):
    """Own a transaction unless the caller already owns the session transaction."""
    if session.in_transaction():
        yield
        return
    async with session.begin():
        yield


async def _load_rows(session: AsyncSession, record_ids: list[UUID] | tuple[UUID, ...]) -> list[LedgerLine]:
    if not record_ids:
        return []
    rows = (await session.scalars(select(LedgerLine).where(LedgerLine.id.in_(set(record_ids))))).all()
    row_by_id = {row.id: row for row in rows}
    missing = [record_id for record_id in record_ids if record_id not in row_by_id]
    if missing:
        raise ValueError(f"ledger records not found: {', '.join(str(record_id) for record_id in missing)}")
    return [row_by_id[record_id] for record_id in record_ids]


async def _settlement_lag(session: AsyncSession, matches: tuple) -> Decimal:
    """Calculate average settlement lag (days between payment and settlement) from matched pairs."""
    if not matches:
        return Decimal("0.00")
    
    # Load all matched line IDs
    all_ids = set()
    for match in matches:
        all_ids.add(match.left_id)
        all_ids.add(match.right_id)
    
    rows = (await session.scalars(select(LedgerLine).where(LedgerLine.id.in_(all_ids)))).all()
    row_by_id = {row.id: row for row in rows}
    
    # Calculate lags between matched pairs
    lags = []
    for match in matches:
        left_row = row_by_id.get(match.left_id)
        right_row = row_by_id.get(match.right_id)
        if left_row and right_row:
            # Lag = absolute days between transaction dates
            lag_days = abs((right_row.txn_date - left_row.txn_date).days)
            lags.append(lag_days)
    
    if not lags:
        return Decimal("0.00")
    
    # Return average as Decimal
    avg_lag = sum(lags) / len(lags)
    return Decimal(str(round(avg_lag, 2)))


def _match_rate(matched: int, total_left: int) -> Decimal:
    if total_left == 0:
        return Decimal("0.00")
    return (Decimal(matched) * Decimal("100") / Decimal(total_left)).quantize(Decimal("0.01"))


def _dollar_match_rate(left_records, matches) -> Decimal:
    total = sum((abs(record.amount) for record in left_records), Decimal("0"))
    matched_ids = {match.left_id for match in matches}
    matched = sum((abs(record.amount) for record in left_records if record.id in matched_ids), Decimal("0"))
    if total == 0:
        return Decimal("0.00")
    return (matched * Decimal("100") / total).quantize(Decimal("0.01"))


async def _summary_for_run(session: AsyncSession, run: ReconciliationRun, left_count: int, right_count: int) -> ReconciliationSummary:
    matches = (await session.scalars(select(Match).where(Match.run_id == run.id))).all()
    exceptions = (await session.scalars(select(ExceptionRecord).where(ExceptionRecord.run_id == run.id))).all()
    tier_breakdown = dict(sorted(Counter(match.tier for match in matches).items()))
    reasons = dict(sorted(Counter(exception.reason_code for exception in exceptions).items()))
    review_count = sum(match.status == MatchStatus.MATCHED_NEEDS_REVIEW.value for match in matches)
    return ReconciliationSummary(
        run_id=run.id, status=run.status, total_left_records=left_count,
        total_right_records=right_count, matched_count=len(matches), review_count=review_count,
        exception_count=len(exceptions), unmatched_count=len(exceptions),
        match_rate=run.match_rate_count or Decimal("0.00"),
        match_rate_dollar=run.match_rate_dollar or Decimal("0.00"), tier_breakdown=tier_breakdown,
        reason_code_breakdown=reasons,
    )


def _summary_from_result(run: ReconciliationRun, result, left_count: int, right_count: int) -> ReconciliationSummary:
    tier_breakdown = dict(sorted(Counter(match.tier for match in result.matches).items()))
    reasons = dict(sorted(Counter(exception.reason_code.value for exception in result.exceptions).items()))
    review_count = sum(match.status == MatchStatus.MATCHED_NEEDS_REVIEW for match in result.matches)
    return ReconciliationSummary(
        run_id=run.id, status=run.status, total_left_records=left_count,
        total_right_records=right_count, matched_count=len(result.matches), review_count=review_count,
        exception_count=len(result.exceptions), unmatched_count=len(result.exceptions),
        match_rate=run.match_rate_count or Decimal("0.00"),
        match_rate_dollar=run.match_rate_dollar or Decimal("0.00"), tier_breakdown=tier_breakdown,
        reason_code_breakdown=reasons,
    )