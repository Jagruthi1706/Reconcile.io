import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import Boolean, CheckConstraint, Date, DateTime, ForeignKey, Index, Integer, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


def uuid_pk_column():
    return mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)


def created_at_column():
    return mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())


class LedgerLine(Base):
    __tablename__ = "ledger_lines"
    __table_args__ = (Index("ix_ledger_lines_source", "source"), Index("ix_ledger_lines_external_ref", "external_ref"))

    id: Mapped[uuid.UUID] = uuid_pk_column()
    source: Mapped[str] = mapped_column(String, nullable=False)
    external_ref: Mapped[str | None] = mapped_column(String)
    amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    txn_date: Mapped[date] = mapped_column(Date, nullable=False)
    entity: Mapped[str | None] = mapped_column(String)
    raw_payload: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    created_at: Mapped[datetime] = created_at_column()


class ReconciliationRun(Base):
    __tablename__ = "reconciliation_runs"
    __table_args__ = (
        CheckConstraint("status IN ('running', 'done')", name="ck_reconciliation_runs_status"),
        Index("ix_reconciliation_runs_status", "status"),
    )

    id: Mapped[uuid.UUID] = uuid_pk_column()
    status: Mapped[str] = mapped_column(String, nullable=False, server_default="running")
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    records_processed: Mapped[int | None] = mapped_column(Integer)
    match_rate_count: Mapped[Decimal | None] = mapped_column(Numeric(5, 2))
    match_rate_dollar: Mapped[Decimal | None] = mapped_column(Numeric(5, 2))
    avg_settlement_lag: Mapped[Decimal | None] = mapped_column(Numeric(5, 2))
    triggered_by: Mapped[str | None] = mapped_column(String)


class Match(Base):
    __tablename__ = "matches"
    __table_args__ = (Index("ix_matches_run_id", "run_id"),)

    id: Mapped[uuid.UUID] = uuid_pk_column()
    run_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("reconciliation_runs.id"), nullable=False)
    line_a_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("ledger_lines.id"), nullable=False)
    line_b_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("ledger_lines.id"), nullable=False)
    tier: Mapped[int] = mapped_column(Integer, nullable=False)
    confidence: Mapped[Decimal] = mapped_column(Numeric(4, 3), nullable=False)
    variance: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime] = created_at_column()


class ExceptionRecord(Base):
    __tablename__ = "exceptions"
    __table_args__ = (Index("ix_exceptions_run_id", "run_id"), Index("ix_exceptions_status", "status"))

    id: Mapped[uuid.UUID] = uuid_pk_column()
    run_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("reconciliation_runs.id"), nullable=False)
    line_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("ledger_lines.id"), nullable=False)
    reason_code: Mapped[str] = mapped_column(String, nullable=False)
    reason_text: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False, server_default="new")
    assignee: Mapped[str | None] = mapped_column(String)
    resolution_note: Mapped[str | None] = mapped_column(Text)
    opened_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class TaxClassification(Base):
    __tablename__ = "tax_classifications"

    id: Mapped[uuid.UUID] = uuid_pk_column()
    gl_line_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("ledger_lines.id"), nullable=False)
    jurisdiction: Mapped[str] = mapped_column(String, nullable=False)
    label: Mapped[str] = mapped_column(String, nullable=False)
    confidence: Mapped[Decimal] = mapped_column(Numeric(4, 3), nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False)
    corrected_label: Mapped[str | None] = mapped_column(String)


class TaxTrainingExample(Base):
    __tablename__ = "tax_training_examples"

    id: Mapped[uuid.UUID] = uuid_pk_column()
    gl_line_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("ledger_lines.id"), nullable=False)
    jurisdiction: Mapped[str] = mapped_column(String, nullable=False)
    label: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime] = created_at_column()


class ForecastSnapshot(Base):
    __tablename__ = "forecast_snapshots"

    id: Mapped[uuid.UUID] = uuid_pk_column()
    run_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("reconciliation_runs.id"), nullable=False)
    generated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    opening_cash: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    weeks: Mapped[list[dict[str, Any]]] = mapped_column(JSONB, nullable=False)
    low_point_week: Mapped[int] = mapped_column(Integer, nullable=False)
    avg_settlement_lag: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)


class GoldenLabel(Base):
    __tablename__ = "golden_labels"

    id: Mapped[uuid.UUID] = uuid_pk_column()
    line_a_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("ledger_lines.id"), nullable=False)
    line_b_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("ledger_lines.id"), nullable=False)
    expected_match: Mapped[bool] = mapped_column(Boolean, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text)


class AccuracyBenchmark(Base):
    __tablename__ = "accuracy_benchmarks"

    id: Mapped[uuid.UUID] = uuid_pk_column()
    engine_version: Mapped[str] = mapped_column(String, nullable=False)
    run_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    precision: Mapped[Decimal] = mapped_column(Numeric(4, 3), nullable=False)
    recall: Mapped[Decimal] = mapped_column(Numeric(4, 3), nullable=False)
    f1: Mapped[Decimal] = mapped_column(Numeric(4, 3), nullable=False)
    tp: Mapped[int] = mapped_column(Integer, nullable=False)
    fp: Mapped[int] = mapped_column(Integer, nullable=False)
    fn: Mapped[int] = mapped_column(Integer, nullable=False)
    tn: Mapped[int] = mapped_column(Integer, nullable=False)


class CopilotQuery(Base):
    __tablename__ = "copilot_queries"

    id: Mapped[uuid.UUID] = uuid_pk_column()
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    question: Mapped[str] = mapped_column(Text, nullable=False)
    answer: Mapped[str] = mapped_column(Text, nullable=False)
    cited_record_ids: Mapped[list[str]] = mapped_column(JSONB, nullable=False)
    mode: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime] = created_at_column()


class AuditLog(Base):
    __tablename__ = "audit_log"

    id: Mapped[uuid.UUID] = uuid_pk_column()
    actor: Mapped[str] = mapped_column(String, nullable=False)
    action: Mapped[str] = mapped_column(String, nullable=False)
    entity_type: Mapped[str] = mapped_column(String, nullable=False)
    entity_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    created_at: Mapped[datetime] = created_at_column()


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = uuid_pk_column()
    email: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    password_hash: Mapped[str | None] = mapped_column(String)
    role: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime] = created_at_column()


class ApplicationSetting(Base):
    __tablename__ = "application_settings"

    key: Mapped[str] = mapped_column(String, primary_key=True)
    value: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())


class RazorpayCredential(Base):
    __tablename__ = "razorpay_credentials"

    id: Mapped[uuid.UUID] = uuid_pk_column()
    key_id: Mapped[str] = mapped_column(String, nullable=False)
    key_secret_encrypted: Mapped[str] = mapped_column(String, nullable=False)
    webhook_secret_encrypted: Mapped[str] = mapped_column(String, nullable=False)
    mode: Mapped[str] = mapped_column(String, nullable=False)
    connected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())


class RazorpayActivity(Base):
    __tablename__ = "razorpay_activity"

    id: Mapped[uuid.UUID] = uuid_pk_column()
    operation: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False)
    response: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    created_at: Mapped[datetime] = created_at_column()
