import json
from collections.abc import Callable
from typing import Protocol

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.models import ExceptionRecord, LedgerLine
from api.models import CopilotQuery
from api.config import get_settings


class CopilotProvider(Protocol):
    def generate(self, question: str, context: str) -> str: ...


class GeminiProvider:
    def __init__(self, api_key: str, model: str, request: Callable[..., object] | None = None) -> None:
        self.api_key = api_key
        self.model = model
        self.request = request or self._request

    def generate(self, question: str, context: str) -> str:
        response = self.request(question=question, context=context, api_key=self.api_key, model=self.model)
        return str(response)

    @staticmethod
    def _request(*, question: str, context: str, api_key: str, model: str) -> str:
        import urllib.parse
        from urllib.request import Request, urlopen
        body = json.dumps({"contents": [{"parts": [{"text": f"Context:\n{context}\nQuestion: {question}"}]}]}).encode()
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{urllib.parse.quote(model)}:generateContent?key={urllib.parse.quote(api_key)}"
        request = Request(url, data=body, headers={"Content-Type": "application/json"}, method="POST")
        with urlopen(request, timeout=10) as response:
            payload = json.loads(response.read().decode())
        return payload["candidates"][0]["content"]["parts"][0]["text"]


async def retrieve_exception_context(session: AsyncSession, question: str) -> list[ExceptionRecord]:
    query = question.strip().lower()
    stmt = select(ExceptionRecord).where(ExceptionRecord.status != "resolved").order_by(ExceptionRecord.opened_at.desc()).limit(20)
    records = (await session.scalars(stmt)).all()
    if "biggest" in query or "largest" in query or not query:
        return records
    terms = [term for term in query.split() if len(term) > 3]
    filtered = [record for record in records if any(term in f"{record.reason_code} {record.reason_text}".lower() for term in terms)]
    return filtered or records


async def answer_structured(session: AsyncSession, question: str, user_id=None) -> dict[str, object]:
    records = await retrieve_exception_context(session, question)
    if not records:
        response = {"answer": "No open exception records were found.", "cited_record_ids": [], "mode": "structured"}
        if user_id is not None:
            session.add(CopilotQuery(user_id=user_id, question=question, answer=response["answer"], cited_record_ids=[], mode="structured"))
            await session.commit()
        return response
    record = records[0]
    line_exists = await session.scalar(select(LedgerLine.id).where(LedgerLine.id == record.line_id))
    cited = [str(record.line_id)] if line_exists is not None else []
    if not cited:
        response = {"answer": "The matching ledger row could not be verified.", "cited_record_ids": [], "mode": "structured"}
    else:
        response = {"answer": f"{record.reason_code} on line {record.line_id}: {record.reason_text}.", "cited_record_ids": cited, "mode": "structured"}
    if user_id is not None:
        session.add(CopilotQuery(user_id=user_id, question=question, answer=response["answer"], cited_record_ids=response["cited_record_ids"], mode="structured"))
        await session.commit()
    return response


async def answer_with_provider(session: AsyncSession, question: str, user_id, provider: CopilotProvider | None) -> dict[str, object]:
    records = await retrieve_exception_context(session, question)
    structured = await answer_structured(session, question)
    if provider is None or not records:
        await _persist_query(session, user_id, question, structured)
        return structured
    allowed_ids = {str(record.line_id) for record in records}
    context = "\n".join(f"[{record.line_id}] {record.reason_code}: {record.reason_text}" for record in records)
    try:
        answer = provider.generate(question, context)
    except Exception:
        await _persist_query(session, user_id, question, structured)
        return structured
    cited = [value for value in allowed_ids if f"[{value}]" in answer]
    if any(token.startswith("[") and token.endswith("]") and token[1:-1] not in allowed_ids for token in answer.split() if token.startswith("[") and token.endswith("]")):
        await _persist_query(session, user_id, question, structured)
        return structured
    if not cited:
        await _persist_query(session, user_id, question, structured)
        return structured
    response = {"answer": answer, "cited_record_ids": cited, "mode": "gemini"}
    await _persist_query(session, user_id, question, response)
    return response


async def _persist_query(session: AsyncSession, user_id, question: str, response: dict[str, object]) -> None:
    session.add(CopilotQuery(user_id=user_id, question=question, answer=response["answer"], cited_record_ids=response["cited_record_ids"], mode=response["mode"]))
    await session.commit()
