from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.models import AccuracyBenchmark, GoldenLabel, LedgerLine
from packages.engine.bench import BenchmarkMetrics, calculate_metrics
from packages.engine.canonical import CanonicalLedgerRecord
from packages.engine.reconciliation import reconcile


async def benchmark_database(session: AsyncSession, engine_version: str = "0.1.0") -> AccuracyBenchmark:
    labels = (await session.scalars(select(GoldenLabel))).all()
    if not labels:
        raise ValueError("cannot benchmark without golden labels")
    ids = {label.line_a_id for label in labels} | {label.line_b_id for label in labels}
    rows = {row.id: row for row in (await session.scalars(select(LedgerLine).where(LedgerLine.id.in_(ids)))).all()}
    expected: list[bool] = []
    predicted: list[bool] = []
    for label in labels:
        left = rows.get(label.line_a_id)
        right = rows.get(label.line_b_id)
        if left is None or right is None:
            raise ValueError("golden label references a missing ledger line")
        result = reconcile([_canonical(left)], [_canonical(right)])
        expected.append(label.expected_match)
        predicted.append(any(match.left_id == left.id and match.right_id == right.id for match in result.matches))
    metrics: BenchmarkMetrics = calculate_metrics(expected, predicted)
    record = AccuracyBenchmark(engine_version=engine_version, precision=metrics.precision, recall=metrics.recall, f1=metrics.f1, tp=metrics.tp, fp=metrics.fp, fn=metrics.fn, tn=metrics.tn)
    session.add(record)
    await session.commit()
    return record


def _canonical(row: LedgerLine) -> CanonicalLedgerRecord:
    return CanonicalLedgerRecord(id=row.id, source=row.source, amount=row.amount, currency=row.currency, txn_date=row.txn_date, external_ref=row.external_ref, description=row.description, entity=row.entity, raw_payload=row.raw_payload, created_at=row.created_at)
