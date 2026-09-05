"""Create the documented core persistence schema.

Revision ID: 0001_initial_schema
Revises:
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0001_initial_schema"
down_revision = None
branch_labels = None
depends_on = None


def uuid_pk():
    return sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()"))


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto")
    op.create_table(
        "ledger_lines", uuid_pk(),
        sa.Column("source", sa.String(), nullable=False), sa.Column("external_ref", sa.String()),
        sa.Column("amount", sa.Numeric(14, 2), nullable=False), sa.Column("currency", sa.String(), nullable=False),
        sa.Column("description", sa.Text()), sa.Column("txn_date", sa.Date(), nullable=False),
        sa.Column("entity", sa.String()), sa.Column("raw_payload", postgresql.JSONB(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_ledger_lines_source", "ledger_lines", ["source"])
    op.create_index("ix_ledger_lines_external_ref", "ledger_lines", ["external_ref"])

    op.create_table(
        "reconciliation_runs", uuid_pk(),
        sa.Column("status", sa.String(), server_default="running", nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("finished_at", sa.DateTime(timezone=True)), sa.Column("records_processed", sa.Integer()),
        sa.Column("match_rate_count", sa.Numeric(5, 2)), sa.Column("match_rate_dollar", sa.Numeric(5, 2)),
        sa.Column("triggered_by", sa.String()),
        sa.CheckConstraint("status IN ('running', 'done')", name="ck_reconciliation_runs_status"),
    )
    op.create_index("ix_reconciliation_runs_status", "reconciliation_runs", ["status"])

    op.create_table(
        "users", uuid_pk(), sa.Column("email", sa.String(), nullable=False, unique=True),
        sa.Column("role", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_table(
        "matches", uuid_pk(),
        sa.Column("run_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("reconciliation_runs.id"), nullable=False),
        sa.Column("line_a_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("ledger_lines.id"), nullable=False),
        sa.Column("line_b_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("ledger_lines.id"), nullable=False),
        sa.Column("tier", sa.Integer(), nullable=False), sa.Column("confidence", sa.Numeric(4, 3), nullable=False),
        sa.Column("variance", sa.Numeric(14, 2), nullable=False), sa.Column("status", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_matches_run_id", "matches", ["run_id"])
    op.create_table(
        "exceptions", uuid_pk(),
        sa.Column("run_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("reconciliation_runs.id"), nullable=False),
        sa.Column("line_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("ledger_lines.id"), nullable=False),
        sa.Column("reason_code", sa.String(), nullable=False), sa.Column("reason_text", sa.Text(), nullable=False),
        sa.Column("status", sa.String(), server_default="new", nullable=False), sa.Column("assignee", sa.String()),
        sa.Column("resolution_note", sa.Text()), sa.Column("opened_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("resolved_at", sa.DateTime(timezone=True)),
    )
    op.create_index("ix_exceptions_run_id", "exceptions", ["run_id"])
    op.create_index("ix_exceptions_status", "exceptions", ["status"])
    op.create_table(
        "tax_classifications", uuid_pk(),
        sa.Column("gl_line_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("ledger_lines.id"), nullable=False),
        sa.Column("jurisdiction", sa.String(), nullable=False), sa.Column("label", sa.String(), nullable=False),
        sa.Column("confidence", sa.Numeric(4, 3), nullable=False), sa.Column("status", sa.String(), nullable=False),
        sa.Column("corrected_label", sa.String()),
    )
    op.create_table(
        "forecast_snapshots", uuid_pk(),
        sa.Column("run_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("reconciliation_runs.id"), nullable=False),
        sa.Column("generated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("opening_cash", sa.Numeric(14, 2), nullable=False), sa.Column("weeks", postgresql.JSONB(), nullable=False),
        sa.Column("low_point_week", sa.Integer(), nullable=False), sa.Column("avg_settlement_lag", sa.Numeric(5, 2), nullable=False),
    )
    op.create_table(
        "golden_labels", uuid_pk(),
        sa.Column("line_a_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("ledger_lines.id"), nullable=False),
        sa.Column("line_b_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("ledger_lines.id"), nullable=False),
        sa.Column("expected_match", sa.Boolean(), nullable=False), sa.Column("notes", sa.Text()),
    )
    op.create_table(
        "accuracy_benchmarks", uuid_pk(),
        sa.Column("engine_version", sa.String(), nullable=False), sa.Column("run_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("precision", sa.Numeric(4, 3), nullable=False), sa.Column("recall", sa.Numeric(4, 3), nullable=False), sa.Column("f1", sa.Numeric(4, 3), nullable=False),
        sa.Column("tp", sa.Integer(), nullable=False), sa.Column("fp", sa.Integer(), nullable=False), sa.Column("fn", sa.Integer(), nullable=False), sa.Column("tn", sa.Integer(), nullable=False),
    )
    op.create_table(
        "copilot_queries", uuid_pk(),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("question", sa.Text(), nullable=False), sa.Column("answer", sa.Text(), nullable=False),
        sa.Column("cited_record_ids", postgresql.JSONB(), nullable=False), sa.Column("mode", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_table(
        "audit_log", uuid_pk(), sa.Column("actor", sa.String(), nullable=False), sa.Column("action", sa.String(), nullable=False),
        sa.Column("entity_type", sa.String(), nullable=False), sa.Column("entity_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("payload", postgresql.JSONB(), nullable=False), sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_table(
        "razorpay_credentials", uuid_pk(), sa.Column("key_id", sa.String(), nullable=False),
        sa.Column("key_secret_encrypted", sa.String(), nullable=False), sa.Column("webhook_secret_encrypted", sa.String(), nullable=False),
        sa.Column("mode", sa.String(), nullable=False), sa.Column("connected_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )


def downgrade() -> None:
    for table in ("razorpay_credentials", "audit_log", "copilot_queries", "accuracy_benchmarks", "golden_labels", "forecast_snapshots", "tax_classifications", "exceptions", "matches", "users", "reconciliation_runs", "ledger_lines"):
        op.drop_table(table)
