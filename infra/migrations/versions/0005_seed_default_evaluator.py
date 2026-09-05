"""Seed a default auditor-viewer user for production evaluator access.

Revision ID: 0005_seed_default_evaluator
Revises: 0004_settlement_lag

Default evaluator credentials:
  Email: evaluator@reconcile.io
  Password: demo-evaluator-password
  Role: auditor-viewer (read-only)

These are demo credentials for the initial evaluator access. They should be
changed or rotated in production after first login.
"""

from alembic import op
import sqlalchemy as sa

revision = "0005_seed_default_evaluator"
down_revision = "0004_settlement_lag"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create default auditor-viewer user if no users exist
    # Password hash for "demo-evaluator-password" (PBKDF2-SHA256, 120000 rounds)
    # This is a well-known test credential documented in the migration.
    password_hash = "pbkdf2_sha256$120000$REwUZLsxTT_d8Kh3jnjA8g==$sDAmxT920M2G3IR19-ilIEPkm58wcTnZGWWMcAtr3mc="
    
    op.get_bind().execute(
        sa.text("""
            INSERT INTO users (email, role, password_hash, created_at)
            SELECT 
                'evaluator@reconcile.io' as email,
                'auditor-viewer' as role,
                :password_hash as password_hash,
                now() as created_at
            WHERE NOT EXISTS (SELECT 1 FROM users)
        """),
        {"password_hash": password_hash}
    )


def downgrade() -> None:
    # Remove the default evaluator user if it exists and is the only user
    op.execute(
        sa.text("""
            DELETE FROM users 
            WHERE email = 'evaluator@reconcile.io' 
            AND role = 'auditor-viewer'
            AND (SELECT COUNT(*) FROM users) = 1
        """)
    )
