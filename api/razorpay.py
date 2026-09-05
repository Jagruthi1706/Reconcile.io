from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException

from api.config import get_settings
from api.ingestion import ingest_payloads
from api.integrations.razorpay import RazorpayAdapter, RazorpayClient, RazorpayIntegrationError
from api.models import RazorpayActivity


def client() -> RazorpayClient:
    return RazorpayClient(get_settings())


async def record_activity(session: AsyncSession, operation: str, response: dict[str, object], status: str = "ok") -> dict[str, object]:
    session.add(RazorpayActivity(id=uuid4(), operation=operation, status=status, response=response, created_at=datetime.now(timezone.utc)))
    await session.commit()
    return response


async def pull_settlements(session: AsyncSession, count: int) -> dict[str, object]:
    response = await provider_call(session, "settlements.pull", lambda: client().list_settlements(count=count))
    await ingest_payloads(session, RazorpayAdapter(), [response])
    from api.tasks import reconcile_all_task
    reconcile_all_task.delay()
    return response


async def provider_call(session: AsyncSession, operation: str, call) -> dict[str, object]:
    try:
        response = dict(call())
    except RazorpayIntegrationError as error:
        await record_activity(session, operation, {"error": type(error).__name__}, "error")
        raise HTTPException(status_code=502, detail="Razorpay Test Mode request failed") from error
    return await record_activity(session, operation, response)
