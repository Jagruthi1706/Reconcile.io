import asyncio
from uuid import UUID

from api.db import SessionLocal
from api.reconciliation import run_reconciliation
from api.models import LedgerLine
from api.worker import celery_app
from sqlalchemy import select


@celery_app.task(name="reconcile.run")
def reconcile_task(left_ids: list[str], right_ids: list[str]) -> str:
    async def run() -> str:
        async with SessionLocal() as session:
            summary = await run_reconciliation(session, [UUID(value) for value in left_ids], [UUID(value) for value in right_ids])
            return str(summary.run_id)

    return asyncio.run(run())


@celery_app.task(name="reconcile.all")
def reconcile_all_task() -> str:
    async def run() -> str:
        async with SessionLocal() as session:
            left_ids = list((await session.scalars(select(LedgerLine.id).where(LedgerLine.source.in_(("bank", "gl"))))).all())
            right_ids = list((await session.scalars(select(LedgerLine.id).where(LedgerLine.source == "razorpay"))).all())
            summary = await run_reconciliation(session, left_ids, right_ids)
            return str(summary.run_id)

    return asyncio.run(run())
