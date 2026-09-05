from uuid import UUID

from fastapi import Depends, FastAPI, File, Form, Header, HTTPException, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.auth import create_access_token, current_user, hash_password, require_write_role, verify_password
from api.accuracy import benchmark_database
from api.copilot import GeminiProvider, answer_with_provider
from api.config import get_settings
from api.db import get_session
from api.exports import board_report_pdf, exceptions_csv, ledger_xlsx
from api.forecast import build_and_persist_forecast
from api.models import AccuracyBenchmark, AuditLog, CopilotQuery, ExceptionRecord, ForecastSnapshot, GoldenLabel, LedgerLine, Match, RazorpayActivity, ReconciliationRun, TaxClassification, User
from api.mutations import override_match, update_exception
from api.reconciliation import run_reconciliation
from api.razorpay import client as razorpay_client, provider_call, pull_settlements
from api.schemas import (
    AuthLoginRequest, AuthLoginResponse, BootstrapRequest, BootstrapResponse, CopilotQueryRequest, CopilotQueryResponse,
    AccuracyResponse, AuditLogResponse, CopilotHistoryResponse, ExceptionResponse, ExceptionUpdateRequest, ExportRequest, ForecastScenarioRequest, ForecastSnapshotResponse, ForecastWeek,
    HealthResponse, LedgerLineResponse, MatchResponse, MatchingRulesResponse, MatchingRulesUpdate,
    MatchOverrideRequest, RunCreateRequest, RunCreateResponse, RunStatusResponse, TaxClassificationResponse,
    RazorpayTestPaymentRequest, TaxCorrectionRequest, TaxRulesResponse, TaxRulesUpdate, UploadResponse, UserResponse,
)
from api.settings import get_setting, matching_rules_response, update_setting
from api.tax import classify_pending_lines, correct_classification
from api.uploads import parse_mapping, persist_csv_upload
from api.webhooks import process_razorpay_webhook

app = FastAPI(title="Reconcile.io API", version="0.1.0", root_path="/api/v1", servers=[{"url": "/api/v1"}])
app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in get_settings().cors_origins.split(",") if origin.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def api_prefix(request, call_next):
    prefix = "/api/v1"
    if request.scope["path"] == prefix or request.scope["path"].startswith(f"{prefix}/"):
        request.scope["path"] = request.scope["path"][len(prefix):] or "/"
    return await call_next(request)


database_session = get_session


def forecast_response(snapshot: ForecastSnapshot) -> ForecastSnapshotResponse:
    return ForecastSnapshotResponse(
        id=snapshot.id, run_id=snapshot.run_id, generated_at=snapshot.generated_at,
        opening_cash=snapshot.opening_cash, weeks=[ForecastWeek(**week) for week in snapshot.weeks],
        low_point_week=snapshot.low_point_week, avg_settlement_lag=snapshot.avg_settlement_lag,
    )


@app.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    return HealthResponse(status="ok")


@app.post("/auth/bootstrap", response_model=BootstrapResponse)
async def bootstrap(payload: BootstrapRequest, session: AsyncSession = Depends(database_session)) -> BootstrapResponse:
    if await session.scalar(select(User.id).limit(1)) is not None:
        raise HTTPException(status_code=409, detail="initial user already exists")
    if payload.role not in {"controller", "analyst", "auditor-viewer"}:
        raise HTTPException(status_code=422, detail="invalid user role")
    user = User(email=payload.email, password_hash=hash_password(payload.password), role=payload.role)
    session.add(user)
    await session.commit()
    return BootstrapResponse(user=UserResponse(email=user.email, role=user.role))


@app.post("/webhooks/razorpay")
async def razorpay_webhook(body: bytes, x_razorpay_signature: str | None = Header(default=None), session: AsyncSession = Depends(database_session)) -> dict[str, str]:
    await process_razorpay_webhook(session, body, x_razorpay_signature)
    from api.tasks import reconcile_all_task
    reconcile_all_task.delay()
    return {"status": "accepted"}


@app.get("/razorpay/orders")
async def razorpay_orders(count: int = Query(default=10, ge=1, le=100), session: AsyncSession = Depends(database_session), _: User = Depends(current_user)) -> dict[str, object]:
    return await provider_call(session, "orders.list", lambda: razorpay_client().list_orders(count=count))


@app.get("/razorpay/payments")
async def razorpay_payments(count: int = Query(default=10, ge=1, le=100), session: AsyncSession = Depends(database_session), _: User = Depends(current_user)) -> dict[str, object]:
    return await provider_call(session, "payments.list", lambda: razorpay_client().list_payments(count=count))


@app.get("/razorpay/refunds")
async def razorpay_refunds(count: int = Query(default=10, ge=1, le=100), session: AsyncSession = Depends(database_session), _: User = Depends(current_user)) -> dict[str, object]:
    return await provider_call(session, "refunds.list", lambda: razorpay_client().list_refunds(count=count))


@app.get("/razorpay/settlements")
async def razorpay_settlements(count: int = Query(default=10, ge=1, le=100), session: AsyncSession = Depends(database_session), _: User = Depends(current_user)) -> dict[str, object]:
    return await provider_call(session, "settlements.list", lambda: razorpay_client().list_settlements(count=count))


@app.get("/razorpay/settlements/recon/combined")
async def razorpay_recon_combined(count: int = Query(default=10, ge=1, le=100), session: AsyncSession = Depends(database_session), _: User = Depends(current_user)) -> dict[str, object]:
    return await provider_call(session, "settlements.recon_combined", lambda: razorpay_client().settlement_reconciliation(count=count))


@app.post("/razorpay/test-payment")
async def razorpay_test_payment(payload: RazorpayTestPaymentRequest, session: AsyncSession = Depends(database_session), _: User = Depends(require_write_role)) -> dict[str, object]:
    # Step 1: Create the order
    order_response = await provider_call(session, "test_payment.create_order", lambda: razorpay_client().create_order(amount=payload.amount, currency=payload.currency, receipt=payload.receipt))
    
    # Step 2: Create and capture a payment (simulates test card payment)
    order_id = order_response.get("id")
    if order_id:
        try:
            # In test mode, create_payment will auto-capture
            payment_response = await provider_call(session, "test_payment.create_payment", lambda: razorpay_client().create_payment(order_id=order_id))
            
            # Step 3: Pull settlements to ingest the payment into ledger_lines
            await pull_settlements(session, 10)
        except Exception:
            # If payment creation fails, at least return the order
            pass
    
    return order_response


@app.post("/razorpay/pull-settlements")
async def razorpay_pull_settlements(count: int = Query(default=100, ge=1, le=100), session: AsyncSession = Depends(database_session), _: User = Depends(require_write_role)) -> dict[str, object]:
    return await pull_settlements(session, count)


@app.get("/razorpay/activity")
async def razorpay_activity(limit: int = Query(default=50, ge=1, le=100), session: AsyncSession = Depends(database_session), _: User = Depends(current_user)) -> list[dict[str, object]]:
    rows = (await session.scalars(select(RazorpayActivity).order_by(RazorpayActivity.created_at.desc()).limit(limit))).all()
    return [{"id": str(row.id), "operation": row.operation, "status": row.status, "response": row.response, "created_at": row.created_at} for row in rows]


@app.get("/ledger/lines", response_model=list[LedgerLineResponse])
async def ledger_lines(source: str | None = None, session: AsyncSession = Depends(database_session), _: User = Depends(current_user)) -> list[LedgerLineResponse]:
    statement = select(LedgerLine).order_by(LedgerLine.txn_date.desc())
    if source is not None:
        statement = statement.where(LedgerLine.source == source)
    rows = (await session.scalars(statement)).all()
    return [LedgerLineResponse.model_validate(row) for row in rows]


@app.get("/ledger/lines/{line_id}", response_model=LedgerLineResponse)
async def ledger_line(line_id: UUID, session: AsyncSession = Depends(database_session), _: User = Depends(current_user)) -> LedgerLineResponse:
    row = await session.get(LedgerLine, line_id)
    if row is None:
        raise HTTPException(status_code=404, detail="ledger line not found")
    return LedgerLineResponse.model_validate(row)

@app.post("/ledger/upload", response_model=UploadResponse)
async def ledger_upload(
    file: UploadFile = File(...),
    source: str = Form(...),
    mapping: str = Form(...),
    session: AsyncSession = Depends(database_session),
    user: User = Depends(require_write_role),
) -> UploadResponse:
    inserted = await persist_csv_upload(session, await file.read(), source, parse_mapping(mapping), file.filename or "upload.csv")
    return UploadResponse(filename=file.filename or "upload.csv", source=source, inserted=inserted)


@app.post("/accuracy/benchmark", response_model=AccuracyResponse)
async def accuracy_benchmark(session: AsyncSession = Depends(database_session), user: User = Depends(require_write_role)) -> AccuracyResponse:
    return AccuracyResponse.model_validate(await benchmark_database(session))


@app.post("/export/csv")
async def export_csv(payload: ExportRequest, session: AsyncSession = Depends(database_session), _: User = Depends(current_user)) -> Response:
    if payload.report_type != "exceptions":
        raise HTTPException(status_code=422, detail="CSV export supports report_type=exceptions")
    return Response(content=await exceptions_csv(session), media_type="text/csv", headers={"Content-Disposition": "attachment; filename=exceptions.csv"})


@app.post("/export/xlsx")
async def export_xlsx(payload: ExportRequest, session: AsyncSession = Depends(database_session), _: User = Depends(current_user)) -> Response:
    if payload.report_type != "ledger":
        raise HTTPException(status_code=422, detail="XLSX export supports report_type=ledger")
    return Response(content=await ledger_xlsx(session), media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", headers={"Content-Disposition": "attachment; filename=ledger.xlsx"})


@app.post("/export/pdf")
async def export_pdf(payload: ExportRequest, session: AsyncSession = Depends(database_session), _: User = Depends(current_user)) -> Response:
    if payload.report_type != "board":
        raise HTTPException(status_code=422, detail="PDF export supports report_type=board")
    return Response(content=await board_report_pdf(session), media_type="application/pdf", headers={"Content-Disposition": "attachment; filename=board-report.pdf"})


@app.get("/accuracy/history", response_model=list[AccuracyResponse])
async def accuracy_history(session: AsyncSession = Depends(database_session), _: User = Depends(current_user)) -> list[AccuracyResponse]:
    rows = (await session.scalars(select(AccuracyBenchmark).order_by(AccuracyBenchmark.run_at.desc()))).all()
    return [AccuracyResponse.model_validate(row) for row in rows]


@app.get("/accuracy/golden-set")
async def accuracy_golden_set(session: AsyncSession = Depends(database_session), _: User = Depends(current_user)) -> list[dict[str, object]]:
    rows = (await session.scalars(select(GoldenLabel))).all()
    return [{"id": str(row.id), "line_a_id": str(row.line_a_id), "line_b_id": str(row.line_b_id), "expected_match": row.expected_match, "notes": row.notes} for row in rows]


@app.post("/auth/login", response_model=AuthLoginResponse)
async def login(payload: AuthLoginRequest, session: AsyncSession = Depends(database_session)) -> AuthLoginResponse:
    user = await session.scalar(select(User).where(User.email == payload.email))
    if user is None or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="invalid credentials")
    return AuthLoginResponse(access_token=create_access_token(user), user=UserResponse(email=user.email, role=user.role))


@app.get("/users/me", response_model=UserResponse)
async def users_me(user: User = Depends(current_user)) -> UserResponse:
    return UserResponse(email=user.email, role=user.role)


@app.get("/settings/matching-rules", response_model=MatchingRulesResponse)
async def get_matching_rules(session: AsyncSession = Depends(database_session), _: User = Depends(current_user)) -> MatchingRulesResponse:
    return MatchingRulesResponse(**matching_rules_response(await get_setting(session, "matching_rules")))


@app.patch("/settings/matching-rules", response_model=MatchingRulesResponse)
async def patch_matching_rules(payload: MatchingRulesUpdate, session: AsyncSession = Depends(database_session), _: User = Depends(require_write_role)) -> MatchingRulesResponse:
    return MatchingRulesResponse(**matching_rules_response(await update_setting(session, "matching_rules", payload.model_dump())))


@app.get("/settings/tax-rules", response_model=TaxRulesResponse)
async def get_tax_rules(session: AsyncSession = Depends(database_session), _: User = Depends(current_user)) -> TaxRulesResponse:
    return TaxRulesResponse(rules=(await get_setting(session, "tax_rules")).get("rules", []))


@app.patch("/settings/tax-rules", response_model=TaxRulesResponse)
async def patch_tax_rules(payload: TaxRulesUpdate, session: AsyncSession = Depends(database_session), _: User = Depends(require_write_role)) -> TaxRulesResponse:
    values = await update_setting(session, "tax_rules", {"rules": [rule.model_dump() for rule in payload.rules]})
    return TaxRulesResponse(rules=values.get("rules", []))


@app.get("/tax/classifications", response_model=list[TaxClassificationResponse])
async def tax_classifications(jurisdiction: str | None = None, status: str | None = None, session: AsyncSession = Depends(database_session), _: User = Depends(current_user)) -> list[TaxClassificationResponse]:
    await classify_pending_lines(session)
    statement = select(TaxClassification)
    if jurisdiction is not None:
        statement = statement.where(TaxClassification.jurisdiction == jurisdiction)
    if status is not None:
        statement = statement.where(TaxClassification.status == status)
    rows = (await session.scalars(statement)).all()
    return [TaxClassificationResponse.model_validate(row) for row in rows]


@app.patch("/tax/classifications/{classification_id}", response_model=TaxClassificationResponse)
async def tax_correction(classification_id: UUID, payload: TaxCorrectionRequest, session: AsyncSession = Depends(database_session), user: User = Depends(require_write_role)) -> TaxClassificationResponse:
    return TaxClassificationResponse.model_validate(await correct_classification(session, classification_id, payload.label, user.email))


@app.get("/forecast/latest", response_model=ForecastSnapshotResponse)
async def forecast_latest(session: AsyncSession = Depends(database_session), _: User = Depends(current_user)) -> ForecastSnapshotResponse:
    snapshot = await session.scalar(select(ForecastSnapshot).order_by(ForecastSnapshot.generated_at.desc()).limit(1))
    if snapshot is None:
        snapshot = await build_and_persist_forecast(session)
    return forecast_response(snapshot)


@app.post("/forecast/scenario", response_model=ForecastSnapshotResponse)
async def forecast_scenario(payload: ForecastScenarioRequest, session: AsyncSession = Depends(database_session), _: User = Depends(current_user)) -> ForecastSnapshotResponse:
    return forecast_response(await build_and_persist_forecast(session, payload.opex_delta_pct, payload.ar_velocity_delta_pct, persist=False))


@app.post("/copilot/query", response_model=CopilotQueryResponse)
async def copilot_query(payload: CopilotQueryRequest, session: AsyncSession = Depends(database_session), user: User = Depends(current_user)) -> CopilotQueryResponse:
    settings = get_settings()
    provider = None
    if payload.mode == "gemini" and settings.gemini_api_key.get_secret_value():
        provider = GeminiProvider(settings.gemini_api_key.get_secret_value(), settings.gemini_model)
    return CopilotQueryResponse(**await answer_with_provider(session, payload.question, user.id, provider))


@app.get("/copilot/history", response_model=list[CopilotHistoryResponse])
async def copilot_history(session: AsyncSession = Depends(database_session), user: User = Depends(current_user)) -> list[CopilotHistoryResponse]:
    rows = (await session.scalars(select(CopilotQuery).where(CopilotQuery.user_id == user.id).order_by(CopilotQuery.created_at.desc()))).all()
    return [CopilotHistoryResponse.model_validate(row) for row in rows]


@app.post("/runs", response_model=RunCreateResponse, status_code=202)
async def create_run(request: RunCreateRequest, session: AsyncSession = Depends(database_session), _: User = Depends(current_user)) -> RunCreateResponse:
    summary = await run_reconciliation(session, request.left_record_ids, request.right_record_ids)
    return RunCreateResponse(run_id=summary.run_id)


@app.get("/runs", response_model=list[RunStatusResponse])
async def list_runs(limit: int = Query(default=50, ge=1, le=100), session: AsyncSession = Depends(database_session), _: User = Depends(current_user)) -> list[RunStatusResponse]:
    rows = (await session.scalars(select(ReconciliationRun).order_by(ReconciliationRun.started_at.desc()).limit(limit))).all()
    return [RunStatusResponse.model_validate(row) for row in rows]


@app.get("/runs/{run_id}", response_model=RunStatusResponse)
async def get_run(run_id: UUID, session: AsyncSession = Depends(database_session), _: User = Depends(current_user)) -> RunStatusResponse:
    run = await session.get(ReconciliationRun, run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="reconciliation run not found")
    return RunStatusResponse.model_validate(run)


@app.get("/runs/{run_id}/matches", response_model=list[MatchResponse])
async def get_run_matches(run_id: UUID, tier: int | None = None, status: str | None = None, min_confidence: float | None = None, session: AsyncSession = Depends(database_session), _: User = Depends(current_user)) -> list[MatchResponse]:
    statement = select(Match).where(Match.run_id == run_id)
    if tier is not None:
        statement = statement.where(Match.tier == tier)
    if status is not None:
        statement = statement.where(Match.status == status)
    if min_confidence is not None:
        statement = statement.where(Match.confidence >= min_confidence)
    rows = (await session.scalars(statement)).all()
    return [MatchResponse.model_validate(row) for row in rows]


@app.post("/matches/{match_id}/override", response_model=MatchResponse)
async def match_override(match_id: UUID, payload: MatchOverrideRequest, session: AsyncSession = Depends(database_session), user: User = Depends(require_write_role)) -> MatchResponse:
    return MatchResponse.model_validate(await override_match(session, match_id, payload.reason, user.email))


@app.get("/runs/{run_id}/exceptions", response_model=list[ExceptionResponse])
async def get_run_exceptions(run_id: UUID, session: AsyncSession = Depends(database_session), _: User = Depends(current_user)) -> list[ExceptionResponse]:
    rows = (await session.scalars(select(ExceptionRecord).where(ExceptionRecord.run_id == run_id))).all()
    return [ExceptionResponse.model_validate(row) for row in rows]


@app.get("/exceptions", response_model=list[ExceptionResponse])
async def list_exceptions(status: str | None = None, reason_code: str | None = None, assignee: str | None = None, source: str | None = None, session: AsyncSession = Depends(database_session), _: User = Depends(current_user)) -> list[ExceptionResponse]:
    statement = select(ExceptionRecord)
    if status is not None:
        statement = statement.where(ExceptionRecord.status == status)
    if reason_code is not None:
        statement = statement.where(ExceptionRecord.reason_code == reason_code)
    if assignee is not None:
        statement = statement.where(ExceptionRecord.assignee == assignee)
    if source is not None:
        statement = statement.join(LedgerLine, ExceptionRecord.line_id == LedgerLine.id).where(LedgerLine.source == source)
    rows = (await session.scalars(statement.order_by(ExceptionRecord.opened_at.desc()))).all()
    return [ExceptionResponse.model_validate(row) for row in rows]


@app.patch("/exceptions/{exception_id}", response_model=ExceptionResponse)
async def exception_update(exception_id: UUID, payload: ExceptionUpdateRequest, session: AsyncSession = Depends(database_session), user: User = Depends(require_write_role)) -> ExceptionResponse:
    return ExceptionResponse.model_validate(await update_exception(session, exception_id, user.email, **payload.model_dump()))


@app.get("/audit", response_model=list[AuditLogResponse])
async def audit(limit: int = Query(default=100, ge=1, le=500), session: AsyncSession = Depends(database_session), _: User = Depends(current_user)) -> list[AuditLogResponse]:
    rows = (await session.scalars(select(AuditLog).order_by(AuditLog.created_at.desc()).limit(limit))).all()
    return [AuditLogResponse.model_validate(row) for row in rows]
