"""Persist Razorpay connector activity.

Revision ID: 0003_razorpay_activity
Revises: 0002_auth_settings
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0003_razorpay_activity"
down_revision = "0002_auth_settings"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "razorpay_activity",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("operation", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("response", postgresql.JSONB(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("razorpay_activity")