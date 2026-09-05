import pytest
from fastapi.testclient import TestClient
from sqlalchemy import Numeric

from api.config import Settings
from api.main import app
from api.models import Base, LedgerLine, Match, ReconciliationRun


def test_health_endpoint() -> None:
    response = TestClient(app).get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_core_models_import_and_foreign_keys() -> None:
    assert Match.__table__.c.run_id.foreign_keys
    assert Match.__table__.c.line_a_id.foreign_keys
    assert "ledger_lines" in Base.metadata.tables


def test_monetary_columns_are_numeric() -> None:
    for column_name in ("amount",):
        assert isinstance(LedgerLine.__table__.c[column_name].type, Numeric)
    assert isinstance(ReconciliationRun.__table__.c.match_rate_count.type, Numeric)


def test_run_status_constraint_is_canonical() -> None:
    constraint = next(c for c in ReconciliationRun.__table__.constraints if c.name == "ck_reconciliation_runs_status")
    assert "running" in str(constraint.sqltext)
    assert "done" in str(constraint.sqltext)
    assert "completed" not in str(constraint.sqltext)


def test_razorpay_mode_rejects_non_test() -> None:
    with pytest.raises(ValueError, match="RAZORPAY_MODE"):
        Settings(razorpay_mode="live")
