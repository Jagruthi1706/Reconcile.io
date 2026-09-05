from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.models import AuditLog, LedgerLine, TaxClassification, TaxTrainingExample


def classify_line(line: LedgerLine) -> tuple[str, str, Decimal]:
    text = f"{line.description or ''} {line.external_ref or ''}".lower()
    if any(term in text for term in ("tax", "vat", "gst")):
        return "taxable", "review", Decimal("0.70")
    if any(term in text for term in ("salary", "payroll", "wage")):
        return "payroll", "auto", Decimal("0.95")
    return "unclassified", "review", Decimal("0.40")


async def classify_pending_lines(session: AsyncSession, line_ids: list[UUID] | None = None) -> int:
    stmt = select(LedgerLine)
    if line_ids:
        stmt = stmt.where(LedgerLine.id.in_(line_ids))
    lines = (await session.scalars(stmt)).all()
    existing_ids = set((await session.scalars(select(TaxClassification.gl_line_id))).all())
    created = 0
    for line in lines:
        if line.id in existing_ids or line.source != "gl":
            continue
        label, status, confidence = classify_line(line)
        session.add(TaxClassification(id=UUID(int=line.id.int), gl_line_id=line.id, jurisdiction=line.entity or "unknown", label=label, status=status, confidence=confidence))
        created += 1
    if created:
        await session.commit()
    return created


async def correct_classification(session: AsyncSession, classification_id: UUID, label: str, actor: str) -> TaxClassification:
    classification = await session.get(TaxClassification, classification_id)
    if classification is None:
        raise ValueError("tax classification not found")
    classification.corrected_label = label
    classification.status = "corrected"
    session.add(TaxTrainingExample(id=uuid4(), gl_line_id=classification.gl_line_id, jurisdiction=classification.jurisdiction, label=label))
    session.add(AuditLog(id=uuid4(), actor=actor, action="tax.correction", entity_type="tax_classification", entity_id=classification.id, payload={"label": label}))
    await session.commit()
    return classification
