"""Persist canonical records without provider or reconciliation decisions."""

from dataclasses import dataclass
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.models import LedgerLine
from packages.engine.canonical import CanonicalLedgerRecord, SourceAdapter


@dataclass(frozen=True, slots=True)
class IngestionSummary:
    inserted: int
    skipped_existing: int
    records: tuple[CanonicalLedgerRecord, ...]


async def ingest_payload(
    session: AsyncSession,
    adapter: SourceAdapter,
    payload: object,
) -> IngestionSummary:
    """Normalize and persist one provider payload in one caller-visible transaction."""
    normalized = adapter.normalize(payload)
    async with session.begin():
        return await persist_canonical_records(session, normalized)


async def ingest_payloads(
    session: AsyncSession,
    adapter: SourceAdapter,
    payloads: list[object] | tuple[object, ...],
) -> IngestionSummary:
    """Normalize and persist a provider batch in one caller-visible transaction."""
    normalized = tuple(record for payload in payloads for record in adapter.normalize(payload))
    async with session.begin():
        return await persist_canonical_records(session, normalized)


async def persist_canonical_records(
    session: AsyncSession,
    records: tuple[CanonicalLedgerRecord, ...] | list[CanonicalLedgerRecord],
) -> IngestionSummary:
    """Persist records inside an already-owned transaction.

    The canonical UUID is the existing ledger primary key and is therefore the
    idempotency key. Existing rows are never updated by ingestion.
    """
    inserted = 0
    skipped_existing = 0
    accepted: list[CanonicalLedgerRecord] = []
    seen_ids: set[UUID] = set()
    record_list = list(records)
    record_ids = {record.id for record in record_list}
    existing_rows = (await session.scalars(select(LedgerLine).where(LedgerLine.id.in_(record_ids)))).all() if record_ids else []
    existing_by_id = {row.id: row for row in existing_rows}
    for record in record_list:
        if record.id in seen_ids:
            skipped_existing += 1
            continue
        seen_ids.add(record.id)
        existing = existing_by_id.get(record.id)
        if existing is not None:
            skipped_existing += 1
            accepted.append(canonical_from_ledger_line(existing))
            continue
        session.add(_ledger_line_from_canonical(record))
        inserted += 1
        accepted.append(record)
    return IngestionSummary(inserted, skipped_existing, tuple(accepted))


def _ledger_line_from_canonical(record: CanonicalLedgerRecord) -> LedgerLine:
    return LedgerLine(
        id=record.id,
        source=record.source,
        external_ref=record.external_ref,
        amount=record.amount,
        currency=record.currency,
        description=record.description,
        txn_date=record.txn_date,
        entity=record.entity,
        raw_payload=dict(record.raw_payload or {}),
        created_at=record.created_at,
    )


def canonical_from_ledger_line(line: LedgerLine) -> CanonicalLedgerRecord:
    """Load a persisted ledger row back into the engine's canonical contract."""
    return CanonicalLedgerRecord(
        id=line.id,
        source=line.source,
        amount=line.amount,
        currency=line.currency,
        txn_date=line.txn_date,
        external_ref=line.external_ref,
        description=line.description,
        entity=line.entity,
        raw_payload=line.raw_payload,
        created_at=line.created_at,
    )
