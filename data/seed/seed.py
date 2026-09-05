"""Load the repository's Razorpay Test Mode fixtures for local demos."""

import asyncio
import json
from pathlib import Path

from api.db import SessionLocal
from api.ingestion import ingest_payloads
from api.integrations.razorpay import RazorpayAdapter

FIXTURE_DIR = Path(__file__).parents[1] / "fixtures" / "razorpay"
FIXTURE_NAMES = ("payments.json", "refunds.json", "settlements.json")


def load_fixture_payloads() -> list[dict[str, object]]:
    return [json.loads((FIXTURE_DIR / name).read_text(encoding="utf-8")) for name in FIXTURE_NAMES]


async def seed() -> tuple[int, int]:
    async with SessionLocal() as session:
        summary = await ingest_payloads(session, RazorpayAdapter(), load_fixture_payloads())
    return summary.inserted, summary.skipped_existing


def main() -> None:
    inserted, skipped_existing = asyncio.run(seed())
    print(f"Seeded Razorpay Test Mode fixtures: {inserted} inserted, {skipped_existing} already present.")


if __name__ == "__main__":
    main()
