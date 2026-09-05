from datetime import datetime, timezone
from uuid import UUID, uuid4

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from api.models import AuditLog, ExceptionRecord, Match


async def override_match(session: AsyncSession, match_id: UUID, reason: str, actor: str) -> Match:
    match = await session.get(Match, match_id)
    if match is None:
        raise HTTPException(status_code=404, detail="match not found")
    previous_status = match.status
    match.status = "overridden"
    session.add(AuditLog(
        id=uuid4(), actor=actor, action="match.override", entity_type="match", entity_id=match.id,
        payload={"reason": reason, "previous_status": previous_status},
        created_at=datetime.now(timezone.utc),
    ))
    await session.commit()
    return match


async def update_exception(
    session: AsyncSession,
    exception_id: UUID,
    actor: str,
    status: str | None = None,
    assignee: str | None = None,
    resolution_note: str | None = None,
) -> ExceptionRecord:
    exception = await session.get(ExceptionRecord, exception_id)
    if exception is None:
        raise HTTPException(status_code=404, detail="exception not found")
    previous = {"status": exception.status, "assignee": exception.assignee, "resolution_note": exception.resolution_note}
    if status is not None:
        exception.status = status
        if status in {"resolved", "written_off"}:
            exception.resolved_at = datetime.now(timezone.utc)
    if assignee is not None:
        exception.assignee = assignee
    if resolution_note is not None:
        exception.resolution_note = resolution_note
    session.add(AuditLog(
        id=uuid4(), actor=actor, action="exception.update", entity_type="exception", entity_id=exception.id,
        payload={"reason": resolution_note or "exception state changed", "previous": previous},
        created_at=datetime.now(timezone.utc),
    ))
    await session.commit()
    return exception
