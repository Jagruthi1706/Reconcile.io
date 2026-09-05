"""Add avg_settlement_lag to reconciliation_runs.

Revision ID: 0004_settlement_lag
Revises: 0003_razorpay_activity
"""
from alembic import op
import sqlalchemy as sa

revision = "0004_settlement_lag"
down_revision = "0003_razorpay_activity"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("reconciliation_runs", sa.Column("avg_settlement_lag", sa.Numeric(5, 2)))


def downgrade() -> None:
    op.drop_column("reconciliation_runs", "avg_settlement_lag")
