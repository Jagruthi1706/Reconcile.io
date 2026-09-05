from datetime import datetime, timezone
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.models import ForecastSnapshot, LedgerLine, ReconciliationRun


def project(opening_cash: Decimal, opex_delta_pct: Decimal, ar_velocity_delta_pct: Decimal) -> dict[str, object]:
    weeks: list[dict[str, Decimal | int]] = []
    projected = opening_cash
    for week in range(1, 14):
        projected = projected * (Decimal("1") - opex_delta_pct / Decimal("100"))
        projected += opening_cash * ar_velocity_delta_pct * Decimal(week) / Decimal("1000")
        weeks.append({"week": week, "projected_cash": projected, "delta_from_opening": projected - opening_cash})
    low_point_week = min(weeks, key=lambda item: item["projected_cash"])["week"]
    return {"opening_cash": opening_cash, "weeks": weeks, "low_point_week": low_point_week, "avg_settlement_lag": Decimal("0.00")}


def json_safe_weeks(weeks: list[dict[str, Decimal | int]]) -> list[dict[str, float | int]]:
    return [
        {
            "week": int(week["week"]),
            "projected_cash": float(week["projected_cash"]),
            "delta_from_opening": float(week["delta_from_opening"]),
        }
        for week in weeks
    ]


async def build_and_persist_forecast(session: AsyncSession, opex_delta_pct: Decimal = Decimal("0"), ar_velocity_delta_pct: Decimal = Decimal("0"), persist: bool = True) -> ForecastSnapshot:
    opening_cash = Decimal(str(await session.scalar(select(LedgerLine.amount).order_by(LedgerLine.created_at.desc()).limit(1)) or Decimal("0")))
    latest_run = await session.scalar(select(ReconciliationRun).order_by(ReconciliationRun.finished_at.desc()).limit(1))
    
    # Retrieve settlement lag from latest run
    avg_settlement_lag = Decimal("0.00")
    if latest_run and latest_run.avg_settlement_lag is not None:
        avg_settlement_lag = latest_run.avg_settlement_lag
    
    values = project(opening_cash, opex_delta_pct, ar_velocity_delta_pct)
    json_weeks = json_safe_weeks(values["weeks"])
    snapshot = ForecastSnapshot(id=uuid4(), run_id=latest_run.id if latest_run else uuid4(), generated_at=datetime.now(timezone.utc), weeks=json_weeks, opening_cash=values["opening_cash"], low_point_week=values["low_point_week"], avg_settlement_lag=avg_settlement_lag)
    if persist:
        session.add(snapshot)
        await session.commit()
    return snapshot
