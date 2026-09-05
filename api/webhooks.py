import hashlib
import hmac
import json
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from api.config import get_settings
from api.ingestion import ingest_payload
from api.integrations.razorpay import RazorpayAdapter


async def process_razorpay_webhook(session: AsyncSession, body: bytes, signature: str | None) -> list[str]:
    secret = get_settings().razorpay_webhook_secret.get_secret_value()
    if not secret or signature is None:
        raise HTTPException(status_code=401, detail="webhook signature required")
    expected = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected, signature):
        raise HTTPException(status_code=401, detail="invalid webhook signature")
    try:
        payload = json.loads(body)
    except json.JSONDecodeError as error:
        raise HTTPException(status_code=422, detail="webhook body must be JSON") from error
    summary = await ingest_payload(session, RazorpayAdapter(), payload)
    await session.commit()
    return [str(record.id) for record in summary.records]
