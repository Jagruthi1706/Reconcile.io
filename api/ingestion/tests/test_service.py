import asyncio
import json
from collections.abc import Mapping
from pathlib import Path

import pytest

from api.ingestion import canonical_from_ledger_line, ingest_payload, ingest_payloads
from api.integrations.razorpay import RazorpayAdapter
from packages.engine.synthetic import SyntheticAdapter, generate_synthetic_dataset
from api.models import LedgerLine
from packages.engine.reconciliation import MatchStatus, reconcile


FIXTURES = Path("data/fixtures/razorpay")


class Transaction:
    async def __aenter__(self) -> "Transaction":
        return self

    async def __aexit__(self, *args: object) -> None:
        return None


class FakeSession:
    def __init__(self) -> None:
        self.rows: dict[object, LedgerLine] = {}
        self.added: list[LedgerLine] = []
        self.begin_calls = 0

    def begin(self) -> Transaction:
        self.begin_calls += 1
        return Transaction()

    async def get(self, model: type[LedgerLine], record_id: object) -> LedgerLine | None:
        return self.rows.get(record_id)

    def add(self, row: LedgerLine) -> None:
        self.rows[row.id] = row
        self.added.append(row)

    async def scalars(self, statement: object):
        class Result:
            def __init__(self, values: list[LedgerLine]) -> None:
                self.values = values

            def all(self) -> list[LedgerLine]:
                return self.values

        return Result(list(self.rows.values()))


def fixture(name: str) -> Mapping[str, object]:
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


def test_provider_fixtures_contain_no_credentials() -> None:
    fixture_text = " ".join(path.read_text(encoding="utf-8") for path in FIXTURES.glob("*.json"))
    assert "RAZORPAY_KEY_SECRET" not in fixture_text
    assert "Authorization" not in fixture_text
    assert "unit-secret" not in fixture_text


@pytest.mark.parametrize("name", ["payments.json", "settlements.json", "refunds.json"])
def test_provider_records_persist_with_canonical_fields(name: str) -> None:
    asyncio.run(_test_provider_records_persist_with_canonical_fields(name))


async def _test_provider_records_persist_with_canonical_fields(name: str) -> None:
    session = FakeSession()
    payload = fixture(name)
    summary = await ingest_payload(session, RazorpayAdapter(), payload)
    row = session.added[0]
    assert summary.inserted == 1
    assert row.source == "razorpay"
    assert row.raw_payload == payload
    assert row.amount == summary.records[0].amount
    assert row.currency == summary.records[0].currency
    assert row.txn_date == summary.records[0].txn_date
    assert row.external_ref == summary.records[0].external_ref
    assert session.begin_calls == 1


def test_duplicate_ingestion_is_idempotent_and_does_not_mutate() -> None:
    asyncio.run(_test_duplicate_ingestion_is_idempotent_and_does_not_mutate())


async def _test_duplicate_ingestion_is_idempotent_and_does_not_mutate() -> None:
    session = FakeSession()
    adapter = RazorpayAdapter()
    payload = fixture("payments.json")
    first = await ingest_payload(session, adapter, payload)
    original = session.added[0]
    changed_payload = payload | {"amount": 99999, "description": "changed replay"}
    second = await ingest_payload(session, adapter, changed_payload)
    assert first.inserted == 1
    assert second.inserted == 0
    assert second.skipped_existing == 1
    assert len(session.added) == 1
    assert session.rows[original.id].amount == original.amount
    assert session.rows[original.id].raw_payload == original.raw_payload


@pytest.mark.parametrize("size", [50, 100, 500])
def test_bulk_ingestion_is_idempotent_for_scaled_batches(size: int) -> None:
    async def run() -> None:
        dataset = generate_synthetic_dataset(record_count=size, seed=size)
        session = FakeSession()
        adapter = SyntheticAdapter()
        first = await ingest_payloads(session, adapter, dataset.left_payloads + dataset.right_payloads)
        second = await ingest_payloads(session, adapter, dataset.left_payloads + dataset.right_payloads)
        assert first.inserted == len(dataset.left_payloads) + len(dataset.right_payloads)
        assert second.inserted == 0
        assert second.skipped_existing == first.inserted
        assert len(session.added) == first.inserted

    asyncio.run(run())


def test_different_provider_objects_remain_distinct() -> None:
    asyncio.run(_test_different_provider_objects_remain_distinct())


async def _test_different_provider_objects_remain_distinct() -> None:
    session = FakeSession()
    adapter = RazorpayAdapter()
    await ingest_payload(session, adapter, fixture("payments.json"))
    await ingest_payload(session, adapter, fixture("refunds.json"))
    assert len(session.added) == 2
    assert len({row.id for row in session.added}) == 2


def test_persisted_rows_load_as_canonical_records_for_existing_matcher() -> None:
    asyncio.run(_test_persisted_rows_load_as_canonical_records_for_existing_matcher())


async def _test_persisted_rows_load_as_canonical_records_for_existing_matcher() -> None:
    session = FakeSession()
    adapter = RazorpayAdapter()
    payment_payload = fixture("payments.json") | {"order_id": "shared-reference"}
    settlement_payload = fixture("settlements.json") | {"amount": 12500, "utr": "shared-reference"}
    await ingest_payload(session, adapter, payment_payload)
    await ingest_payload(session, adapter, settlement_payload)
    records = [canonical_from_ledger_line(row) for row in session.added]
    result = reconcile(records[:1], records[1:])
    assert result.matches[0].tier == 1
    assert result.matches[0].status == MatchStatus.AUTO_MATCHED
    assert not result.exceptions