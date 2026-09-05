import csv
import io
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.models import ExceptionRecord, LedgerLine


def _rows_csv(rows: list[ExceptionRecord]) -> str:
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(("id", "run_id", "line_id", "reason_code", "reason_text", "status", "assignee", "opened_at", "resolved_at"))
    for row in rows:
        writer.writerow((row.id, row.run_id, row.line_id, row.reason_code, row.reason_text, row.status, row.assignee or "", row.opened_at, row.resolved_at or ""))
    return output.getvalue()


async def exceptions_csv(session: AsyncSession) -> str:
    rows = (await session.scalars(select(ExceptionRecord).order_by(ExceptionRecord.opened_at.desc()))).all()
    return _rows_csv(rows)


async def ledger_xlsx(session: AsyncSession) -> bytes:
    from openpyxl import Workbook

    rows = (await session.scalars(select(LedgerLine).order_by(LedgerLine.txn_date.desc()))).all()
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Ledger"
    sheet.append(("id", "source", "external_ref", "amount", "currency", "description", "txn_date", "entity", "raw_payload"))
    for row in rows:
        sheet.append((str(row.id), row.source, row.external_ref, float(row.amount), row.currency, row.description, row.txn_date, row.entity, str(row.raw_payload)))
    output = io.BytesIO()
    workbook.save(output)
    return output.getvalue()


async def board_report_pdf(session: AsyncSession) -> bytes:
    from weasyprint import HTML

    exceptions = (await session.scalars(select(ExceptionRecord).order_by(ExceptionRecord.opened_at.desc()))).all()
    html = "<h1>Reconcile.io Board Report</h1><p>Exception summary from persisted records.</p><table><tr><th>Line</th><th>Reason</th><th>Status</th></tr>"
    html += "".join(f"<tr><td>{row.line_id}</td><td>{row.reason_code}: {row.reason_text}</td><td>{row.status}</td></tr>" for row in exceptions)
    html += "</table>"
    return HTML(string=html).write_pdf()
