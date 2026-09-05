"""Opt-in PostgreSQL integration coverage for the persisted pipeline.

Set RECONCILE_TEST_DATABASE_URL to an isolated PostgreSQL async URL to run.
These tests never use the application's default database automatically.
"""

import asyncio
import os
import time
from collections import Counter
from decimal import Decimal
from uuid import UUID, uuid4

import httpx
import pytest
from sqlalchemy import delete, event, func, select
from sqlalchemy.exc import StatementError
from sqlalchemy.pool import NullPool
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

pytest.importorskip("asyncpg")
TEST_DATABASE_URL = os.getenv("RECONCILE_TEST_DATABASE_URL")
if not TEST_DATABASE_URL:
    pytest.skip("RECONCILE_TEST_DATABASE_URL is not configured", allow_module_level=True)

from api.ingestion import canonical_from_ledger_line, ingest_payloads, persist_canonical_records
from api.integrations.razorpay import RazorpayAdapter
from api.auth import current_user
from api.main import app, database_session
from api.models import Base, ExceptionRecord, LedgerLine, Match, ReconciliationRun, User
from api.reconciliation import run_reconciliation
from packages.engine.canonical import CanonicalLedgerRecord
from packages.engine.synthetic import SyntheticAdapter, generate_synthetic_dataset


@pytest.fixture(scope="module")
def database():
    # Each test uses asyncio.run(), creating a fresh Windows event loop. A
    # pooled asyncpg connection cannot safely cross those loop boundaries.
    engine = create_async_engine(TEST_DATABASE_URL, poolclass=NullPool, pool_pre_ping=True)
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async def setup() -> None:
        async with engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)

    asyncio.run(setup())
    yield engine, session_factory

    async def teardown() -> None:
        async with engine.begin() as connection:
            await connection.run_sync(Base.metadata.drop_all)
        await engine.dispose()

    asyncio.run(teardown())


async def clear_database(session: AsyncSession) -> None:
    await session.execute(delete(Match))
    await session.execute(delete(ExceptionRecord))
    await session.execute(delete(ReconciliationRun))
    await session.execute(delete(LedgerLine))
    await session.commit()


async def persisted_count(session: AsyncSession, model: type[object]) -> int:
    return int((await session.scalar(select(func.count()).select_from(model))) or 0)


async def run_size(database, size: int):
    engine, session_factory = database
    dataset = generate_synthetic_dataset(record_count=size, seed=size)
    async with session_factory() as session:
        await clear_database(session)
        counters: Counter[str] = Counter()

        def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
            counters["sql"] += 1
            normalized = statement.lstrip().upper()
            if normalized.startswith("SELECT"):
                counters["select"] += 1
            if normalized.startswith("INSERT"):
                counters["insert"] += 1

        event.listen(engine.sync_engine, "before_cursor_execute", before_cursor_execute)
        started = time.perf_counter()
        first = await ingest_payloads(
            session,
            SyntheticAdapter(),
            dataset.left_payloads + dataset.right_payloads,
        )
        ingestion_seconds = time.perf_counter() - started
        event.remove(engine.sync_engine, "before_cursor_execute", before_cursor_execute)

        expected_rows = len(dataset.left_payloads) + len(dataset.right_payloads)
        assert first.inserted == expected_rows
        assert await persisted_count(session, LedgerLine) == expected_rows
        assert await session.scalar(select(func.count(func.distinct(LedgerLine.id)))) == expected_rows
        assert counters["select"] <= 2

        sample = (await session.scalars(select(LedgerLine).limit(1))).one()
        canonical = canonical_from_ledger_line(sample)
        assert isinstance(canonical.amount, Decimal)
        assert canonical.raw_payload
        assert canonical.id == sample.id
        assert canonical.currency == sample.currency
        assert canonical.txn_date == sample.txn_date

        left_ids = tuple(canonical_record.id for canonical_record in dataset.left_records)
        right_ids = tuple(canonical_record.id for canonical_record in dataset.right_records)
        started = time.perf_counter()
        summary = await run_reconciliation(session, left_ids, right_ids)
        reconciliation_seconds = time.perf_counter() - started
        assert summary.total_left_records == len(left_ids)
        assert summary.total_right_records == len(right_ids)
        assert await persisted_count(session, Match) == summary.matched_count
        assert await persisted_count(session, ExceptionRecord) == summary.exception_count

        await session.rollback()
        second_ingest = await ingest_payloads(
            session,
            SyntheticAdapter(),
            dataset.left_payloads + dataset.right_payloads,
        )
        assert second_ingest.inserted == 0
        assert second_ingest.skipped_existing == expected_rows
        assert await persisted_count(session, LedgerLine) == expected_rows

        second_summary = await run_reconciliation(session, left_ids, right_ids)
        assert second_summary == summary
        return summary, ingestion_seconds, reconciliation_seconds, counters


@pytest.mark.parametrize("size", [50, 100, 500])
def test_postgres_scale_idempotency_and_round_trip(database, size: int) -> None:
    summary, ingestion_seconds, reconciliation_seconds, counters = asyncio.run(run_size(database, size))
    assert summary.status == "done"
    assert summary.match_rate >= Decimal("0")
    assert ingestion_seconds >= 0
    assert reconciliation_seconds >= 0
    assert counters["select"] <= 2


def test_postgres_transaction_rolls_back_partial_batch(database) -> None:
    _, session_factory = database

    async def run() -> None:
        async with session_factory() as session:
            await clear_database(session)
            valid = CanonicalLedgerRecord(
                id=uuid4(), source="synthetic", amount=Decimal("10.00"), currency="USD",
                txn_date=generate_synthetic_dataset(record_count=1).left_records[0].txn_date,
                external_ref="rollback-valid", raw_payload={"id": "rollback-valid"},
            )
            invalid = CanonicalLedgerRecord(
                id=uuid4(), source="synthetic", amount=Decimal("11.00"), currency="USD",
                txn_date=valid.txn_date, external_ref="rollback-invalid",
                raw_payload={"not_json": object()},
            )
            with pytest.raises(StatementError, match="not JSON serializable"):
                async with session.begin():
                    await persist_canonical_records(session, [valid, invalid])
            assert await persisted_count(session, LedgerLine) == 0

    asyncio.run(run())


def test_postgres_api_routes_reflect_persisted_state(database) -> None:
    _, session_factory = database

    async def run() -> None:
        dataset = generate_synthetic_dataset(record_count=50, seed=501)
        async with session_factory() as session:
            await clear_database(session)
            await ingest_payloads(session, SyntheticAdapter(), dataset.left_payloads + dataset.right_payloads)
            left_ids = [str(record.id) for record in dataset.left_records]
            right_ids = [str(record.id) for record in dataset.right_records]

            async def override_session():
                yield session

            app.dependency_overrides[database_session] = override_session
            app.dependency_overrides[current_user] = lambda: User(id=uuid4(), email="integration@example.com", role="controller")
            try:
                transport = httpx.ASGITransport(app=app)
                async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
                    response = await client.post("/runs", json={"left_record_ids": left_ids, "right_record_ids": right_ids})
                    assert response.status_code == 202
                    run_id = response.json()["run_id"]
                    detail = await client.get(f"/runs/{run_id}")
                    matches = await client.get(f"/runs/{run_id}/matches")
                    exceptions = await client.get(f"/runs/{run_id}/exceptions")
                    listed = await client.get("/runs")
                    queue = await client.get("/exceptions")
                    assert detail.status_code == 200
                    assert matches.status_code == 200
                    assert exceptions.status_code == 200
                    assert listed.status_code == 200
                    assert queue.status_code == 200
                    assert detail.json()["status"] == "done"
                    assert len(matches.json()) + len(exceptions.json()) == len(dataset.left_records)
                    assert len(queue.json()) >= len(exceptions.json())
            finally:
                app.dependency_overrides.clear()

    asyncio.run(run())


def test_razorpay_fixture_can_persist_when_database_is_available(database) -> None:
    _, session_factory = database

    async def run() -> None:
        payload = {
            "entity": "payment", "id": "pay_db_fixture", "amount": 12500,
            "currency": "INR", "order_id": "order_db_fixture", "created_at": 1725456000,
        }
        async with session_factory() as session:
            await clear_database(session)
            records = RazorpayAdapter().normalize(payload)
            summary = await persist_canonical_records(session, records)
            await session.commit()
            assert summary.inserted == 1
            row = await session.get(LedgerLine, records[0].id)
            assert row is not None
            assert row.amount == Decimal("125.00")
            assert row.currency == "INR"
            assert row.raw_payload["id"] == "pay_db_fixture"

    asyncio.run(run())
