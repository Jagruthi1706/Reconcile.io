import asyncio
import re
from datetime import date, datetime, timezone
from decimal import Decimal
from pathlib import Path
from uuid import uuid4

from api.auth import create_access_token, decode_access_token, hash_password, require_write_role, verify_password
from api.accuracy import _canonical
from api.config import Settings
from api.copilot import GeminiProvider, answer_structured
from api.forecast import project
from api.models import AuditLog, ExceptionRecord, LedgerLine, Match, User
from api.mutations import override_match, update_exception
from api.settings import matching_rules_response
from api.tax import classify_line
from api.uploads import parse_csv
from api.worker import celery_app
from api.main import app


def ledger(description: str, source: str = "gl") -> LedgerLine:
    return LedgerLine(
        id=uuid4(), source=source, external_ref=None, amount=Decimal("10.00"), currency="USD",
        txn_date=date(2026, 1, 1), description=description, raw_payload={}, entity="US-CA",
    )


def test_tax_engine_is_deterministic_and_confidence_gated() -> None:
    assert classify_line(ledger("monthly payroll")) == ("payroll", "auto", Decimal("0.95"))
    assert classify_line(ledger("unknown vendor")) == ("unclassified", "review", Decimal("0.40"))


def test_railway_postgres_urls_normalize_to_asyncpg_without_losing_ssl_options() -> None:
    settings = Settings(database_url="postgresql://user:password@host:5432/db?sslmode=require&channel_binding=require")
    assert settings.database_url == "postgresql+asyncpg://user:password@host:5432/db?ssl=require"


def test_documented_evaluator_credentials_match_seeded_password_hash() -> None:
    evaluator_hash = "pbkdf2_sha256$120000$REwUZLsxTT_d8Kh3jnjA8g==$sDAmxT920M2G3IR19-ilIEPkm58wcTnZGWWMcAtr3mc="
    assert verify_password("demo-evaluator-password", evaluator_hash)
    assert not verify_password("wrong-password", evaluator_hash)


def test_alembic_revision_ids_fit_version_column_limit() -> None:
    migration_dir = Path(__file__).parents[1] / "infra" / "migrations" / "versions"
    revision_ids = []
    for migration in migration_dir.glob("*.py"):
        match = re.search(r'^revision\s*=\s*["\']([^"\']+)["\']', migration.read_text(), re.MULTILINE)
        if match:
            revision_ids.append(match.group(1))
    assert revision_ids
    assert all(len(revision_id) <= 32 for revision_id in revision_ids)


def test_celery_worker_uses_configured_redis_and_registers_reconciliation_task() -> None:
    assert celery_app.conf.broker_url == celery_app.conf.result_backend
    assert "api.tasks" in celery_app.conf.imports


def test_openapi_advertises_the_documented_api_v1_server() -> None:
    assert app.servers == [{"url": "/api/v1"}]


def test_every_protected_write_route_uses_the_write_role_guard() -> None:
    expected = {
        ("/ledger/upload", "POST"), ("/accuracy/benchmark", "POST"),
        ("/settings/matching-rules", "PATCH"), ("/settings/tax-rules", "PATCH"),
        ("/tax/classifications/{classification_id}", "PATCH"),
        ("/razorpay/test-payment", "POST"), ("/razorpay/pull-settlements", "POST"),
        ("/matches/{match_id}/override", "POST"), ("/exceptions/{exception_id}", "PATCH"),
    }
    protected = set()
    for route in app.routes:
        if not hasattr(route, "dependant"):
            continue
        dependencies = {dependency.call for dependency in route.dependant.dependencies}
        for method in getattr(route, "methods", set()):
            if require_write_role in dependencies:
                protected.add((route.path, method))
    assert protected == expected


def test_gemini_provider_uses_mocked_response_without_needing_a_key() -> None:
    provider = GeminiProvider("unused-in-test", "gemini-test", request=lambda **_: "[line-1] verified")
    assert provider.generate("question", "[line-1] context") == "[line-1] verified"


def test_forecast_engine_projects_thirteen_weeks_and_finds_low_point() -> None:
    result = project(Decimal("250000"), Decimal("2"), Decimal("5"))
    assert len(result["weeks"]) == 13
    assert 1 <= result["low_point_week"] <= 13
    assert result["opening_cash"] == Decimal("250000")


def test_jwt_round_trip_and_password_hashing() -> None:
    user = User(id=uuid4(), email="analyst@example.com", password_hash=hash_password("secret"), role="analyst")
    assert verify_password("secret", user.password_hash)
    assert not verify_password("wrong", user.password_hash)
    claims = decode_access_token(create_access_token(user))
    assert claims["sub"] == str(user.id)
    assert claims["role"] == "analyst"


def test_settings_response_preserves_persisted_value_types() -> None:
    response = matching_rules_response({
        "match_auto_accept_confidence": "0.91",
        "match_amount_tolerance_pct": "1.25",
        "match_date_window_days": 4,
    })
    assert response == {
        "match_auto_accept_confidence": Decimal("0.91"),
        "match_amount_tolerance_pct": Decimal("1.25"),
        "match_date_window_days": 4,
    }


def test_copilot_verifies_cited_ledger_row() -> None:
    line = ledger("missing counterpart")
    exception = ExceptionRecord(
        id=uuid4(), run_id=uuid4(), line_id=line.id, reason_code="NO_COUNTERPART",
        reason_text="No matching ledger row", status="new", assignee=None,
        resolution_note=None, opened_at=datetime.now(timezone.utc), resolved_at=None,
    )

    class Result:
        def all(self):
            return [exception]

    class Session:
        async def scalars(self, statement):
            return Result()

        async def scalar(self, statement):
            return line.id

    result = asyncio.run(answer_structured(Session(), "what is the exception?"))
    assert result["cited_record_ids"] == [str(line.id)]
    assert "NO_COUNTERPART" in result["answer"]


def test_csv_upload_parser_maps_and_preserves_source_row() -> None:
    content = b"ref,total,ccy,posted,memo\nINV-7,125.50,USD,2026-01-15,office supplies\n"
    records = parse_csv(content, "gl", {
        "external_ref": "ref", "amount": "total", "currency": "ccy",
        "txn_date": "posted", "description": "memo",
    })
    assert len(records) == 1
    assert records[0].external_ref == "INV-7"
    assert records[0].amount == Decimal("125.50")
    assert records[0].raw_payload == {"ref": "INV-7", "total": "125.50", "ccy": "USD", "posted": "2026-01-15", "memo": "office supplies"}


def test_accuracy_canonical_conversion_preserves_decision_fields() -> None:
    row = ledger("invoice INV-7")
    converted = _canonical(row)
    assert converted.id == row.id
    assert converted.amount == row.amount
    assert converted.raw_payload == row.raw_payload


def test_mutations_update_rows_and_write_audit_events() -> None:
    match = Match(id=uuid4(), run_id=uuid4(), line_a_id=uuid4(), line_b_id=uuid4(), tier=1, confidence=Decimal("0.99"), variance=Decimal("0"), status="auto-matched")
    exception = ExceptionRecord(
        id=uuid4(), run_id=uuid4(), line_id=uuid4(), reason_code="NO_COUNTERPART",
        reason_text="missing", status="new", assignee=None, resolution_note=None,
        opened_at=datetime.now(timezone.utc), resolved_at=None,
    )

    class Session:
        def __init__(self):
            self.rows = {match.id: match, exception.id: exception}
            self.added = []

        async def get(self, model, key):
            return self.rows.get(key)

        def add(self, item):
            self.added.append(item)

        async def commit(self):
            return None

    async def run():
        session = Session()
        await override_match(session, match.id, "manual evidence", "controller@example.com")
        await update_exception(session, exception.id, "analyst@example.com", status="resolved", resolution_note="cleared")
        return session

    session = asyncio.run(run())
    assert match.status == "overridden"
    assert exception.status == "resolved"
    assert exception.resolution_note == "cleared"
    assert len([item for item in session.added if isinstance(item, AuditLog)]) == 2
