"""Ensure the documented evaluator account exists after migration 0005.

Revision ID: 0006_evaluator_creds
Revises: 0005_seed_default_evaluator
"""

from alembic import op
import sqlalchemy as sa

revision = "0006_evaluator_creds"
down_revision = "0005_seed_default_evaluator"
branch_labels = None
depends_on = None


def upgrade() -> None:
    password_hash = "pbkdf2_sha256$120000$REwUZLsxTT_d8Kh3jnjA8g==$sDAmxT920M2G3IR19-ilIEPkm58wcTnZGWWMcAtr3mc="
    op.get_bind().execute(
        sa.text("""
            INSERT INTO users (email, role, password_hash, created_at)
            VALUES ('evaluator@reconcile.io', 'auditor-viewer', :password_hash, now())
            ON CONFLICT (email) DO UPDATE
            SET role = 'auditor-viewer', password_hash = :password_hash
        """),
        {"password_hash": password_hash},
    )


def downgrade() -> None:
    op.execute(
        sa.text("DELETE FROM users WHERE email = 'evaluator@reconcile.io'")
    )