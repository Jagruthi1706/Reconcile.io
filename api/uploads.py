import csv
import io
import json
from datetime import date
from decimal import Decimal, InvalidOperation
from uuid import UUID, uuid5

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from api.ingestion import ingest_payloads
from api.models import AuditLog
from packages.engine.canonical import CanonicalLedgerRecord

_UPLOAD_NAMESPACE = UUID("f7b4a3c2-82cd-4ec5-8f4a-8b0b3b0b3295")
_REQUIRED_FIELDS = {"external_ref", "amount", "currency", "txn_date"}


def parse_csv(content: bytes, source: str, mapping: dict[str, str]) -> list[CanonicalLedgerRecord]:
    if source not in {"bank", "gl"}:
        raise HTTPException(status_code=422, detail="source must be bank or gl")
    missing = _REQUIRED_FIELDS - set(mapping)
    if missing:
        raise HTTPException(status_code=422, detail=f"missing mapping fields: {', '.join(sorted(missing))}")
    try:
        rows = csv.DictReader(io.StringIO(content.decode("utf-8-sig")))
    except UnicodeDecodeError as error:
        raise HTTPException(status_code=422, detail="CSV must be UTF-8 encoded") from error
    if rows.fieldnames is None or any(column not in rows.fieldnames for column in mapping.values()):
        raise HTTPException(status_code=422, detail="mapping references a missing CSV column")
    records: list[CanonicalLedgerRecord] = []
    for row_number, row in enumerate(rows, start=2):
        try:
            external_ref = _required(row, mapping["external_ref"])
            amount = Decimal(_required(row, mapping["amount"]))
            txn_date = date.fromisoformat(_required(row, mapping["txn_date"]))
            currency = _required(row, mapping["currency"])
        except (InvalidOperation, ValueError) as error:
            raise HTTPException(status_code=422, detail=f"invalid CSV row {row_number}") from error
        records.append(CanonicalLedgerRecord(
            id=uuid5(_UPLOAD_NAMESPACE, f"{source}:{external_ref}"), source=source,
            external_ref=external_ref, amount=amount, currency=currency, txn_date=txn_date,
            description=row.get(mapping.get("description", "")) if mapping.get("description") else None,
            entity=row.get(mapping.get("entity", "")) if mapping.get("entity") else None,
            raw_payload=dict(row),
        ))
    return records


async def persist_csv_upload(session: AsyncSession, content: bytes, source: str, mapping: dict[str, str], filename: str) -> int:
    records = parse_csv(content, source, mapping)
    summary = await ingest_payloads(session, CsvAdapter(records), [None])
    session.add(AuditLog(
        id=uuid5(_UPLOAD_NAMESPACE, f"upload:{filename}:{source}"), actor="system",
        action="ledger.upload", entity_type="ledger_upload", entity_id=summary.records[0].id if summary.records else uuid5(_UPLOAD_NAMESPACE, filename),
        payload={"filename": filename, "source": source, "records": len(records)},
    ))
    await session.commit()
    return summary.inserted


class CsvAdapter:
    def __init__(self, records: list[CanonicalLedgerRecord]) -> None:
        self.records = records

    def normalize(self, payload: object):
        return self.records


def parse_mapping(value: str) -> dict[str, str]:
    try:
        mapping = json.loads(value)
    except json.JSONDecodeError as error:
        raise HTTPException(status_code=422, detail="mapping must be a JSON object") from error
    if not isinstance(mapping, dict) or not all(isinstance(key, str) and isinstance(column, str) for key, column in mapping.items()):
        raise HTTPException(status_code=422, detail="mapping must map field names to CSV columns")
    return mapping


def _required(row: dict[str, str | None], column: str) -> str:
    value = row.get(column)
    if value is None or not value.strip():
        raise ValueError(column)
    return value.strip()
