"""Load the repository's Razorpay Test Mode fixtures for local demos."""

import asyncio
import json
from pathlib import Path

from sqlalchemy import select

from api.db import SessionLocal
from api.ingestion import ingest_payloads
from api.integrations.razorpay import RazorpayAdapter
from api.forecast import build_and_persist_forecast
from api.models import LedgerLine
from api.reconciliation import run_reconciliation
from api.tax import classify_pending_lines
from packages.engine.synthetic import SyntheticAdapter

FIXTURE_ROOT = Path(__file__).parents[1] / "fixtures"
RAZORPAY_FIXTURE_DIR = FIXTURE_ROOT / "razorpay"
DEMO_FIXTURE_DIR = FIXTURE_ROOT / "demo"
RAZORPAY_FIXTURE_NAMES = ("payments.json", "refunds.json", "settlements.json")
DEMO_FIXTURE_NAMES = ("bank.json", "gl.json")


def load_fixture_payloads() -> list[dict[str, object]]:
    return [json.loads((RAZORPAY_FIXTURE_DIR / name).read_text(encoding="utf-8")) for name in RAZORPAY_FIXTURE_NAMES]


def load_demo_payloads(name: str) -> list[dict[str, object]]:
    return json.loads((DEMO_FIXTURE_DIR / name).read_text(encoding="utf-8"))


async def seed() -> tuple[int, int, int, int]:
    async with SessionLocal() as session:
        razorpay_summary = await ingest_payloads(session, RazorpayAdapter(), load_fixture_payloads())
        demo_summary = await ingest_payloads(
            session,
            SyntheticAdapter(),
            load_demo_payloads("bank.json") + load_demo_payloads("gl.json"),
        )
        bank_ids = list((await session.scalars(select(LedgerLine.id).where(LedgerLine.source == "bank"))).all())
        gl_ids = list((await session.scalars(select(LedgerLine.id).where(LedgerLine.source == "gl"))).all())
        razorpay_ids = list((await session.scalars(select(LedgerLine.id).where(LedgerLine.source == "razorpay"))).all())
        summary = await run_reconciliation(session, bank_ids + gl_ids, razorpay_ids)
        await classify_pending_lines(session, gl_ids)
        await build_and_persist_forecast(session)
        await session.commit()
    return razorpay_summary.inserted + demo_summary.inserted, razorpay_summary.skipped_existing + demo_summary.skipped_existing, summary.matched_count, summary.exception_count


def main() -> None:
    inserted, skipped_existing, matched, exceptions = asyncio.run(seed())
    print(f"Seeded demo fixtures: {inserted} inserted, {skipped_existing} already present; reconciliation matches={matched}, exceptions={exceptions}.")


if __name__ == "__main__":
    main()
