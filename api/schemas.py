from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class HealthResponse(BaseModel):
    status: str


class LedgerLineResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    source: str
    external_ref: str | None = None
    amount: Decimal
    currency: str
    description: str | None = None
    txn_date: date
    entity: str | None = None
    raw_payload: dict


class BootstrapRequest(BaseModel):
    email: str
    password: str = Field(min_length=12)
    role: str = "controller"


class RunCreateResponse(BaseModel):
    run_id: UUID


class RunCreateRequest(BaseModel):
    left_record_ids: list[UUID] = Field(default_factory=list)
    right_record_ids: list[UUID] = Field(default_factory=list)


class RunStatusResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    status: str
    started_at: datetime
    records_processed: int | None = None
    match_rate_count: float | None = None
    match_rate_dollar: float | None = None
    finished_at: datetime | None = None
    auto_matched: int = 0
    needs_review: int = 0
    exceptions: int = 0


class MatchResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    line_a_id: UUID
    line_b_id: UUID
    tier: int
    confidence: float
    variance: float
    status: str


class MatchOverrideRequest(BaseModel):
    reason: str = Field(min_length=1, max_length=2000)


class ExceptionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    run_id: UUID
    line_id: UUID
    reason_code: str
    reason_text: str
    status: str
    assignee: str | None = None
    opened_at: datetime | None = None
    resolved_at: datetime | None = None


class ExceptionUpdateRequest(BaseModel):
    status: str | None = Field(default=None, pattern="^(new|investigating|resolved|written_off)$")
    assignee: str | None = None
    resolution_note: str | None = None


class AuditLogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    actor: str
    action: str
    entity_type: str
    entity_id: UUID
    payload: dict
    created_at: datetime


class TaxClassificationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    gl_line_id: UUID
    jurisdiction: str
    label: str
    status: str
    confidence: float
    corrected_label: str | None = None


class TaxCorrectionRequest(BaseModel):
    label: str = Field(min_length=1, max_length=200)


class ForecastWeek(BaseModel):
    week: int
    projected_cash: float
    delta_from_opening: float


class ForecastSnapshotResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID | None = None
    run_id: UUID | str | None = None
    generated_at: datetime | None = None
    opening_cash: float
    weeks: list[ForecastWeek]
    low_point_week: int
    avg_settlement_lag: float


class CopilotQueryRequest(BaseModel):
    question: str
    mode: str = Field(default="structured", pattern="^(structured|gemini)$")


class CopilotQueryResponse(BaseModel):
    answer: str
    cited_record_ids: list[str]
    mode: str


class CopilotHistoryResponse(CopilotQueryResponse):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    question: str
    created_at: datetime


class UserResponse(BaseModel):
    email: str
    role: str


class BootstrapResponse(BaseModel):
    user: UserResponse


class RazorpayTestPaymentRequest(BaseModel):
    amount: int = Field(gt=0)
    currency: str = Field(min_length=3, max_length=3)
    receipt: str = Field(min_length=1, max_length=40)


class AuthLoginRequest(BaseModel):
    email: str
    password: str


class AuthLoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class MatchingRulesResponse(BaseModel):
    match_auto_accept_confidence: float
    match_amount_tolerance_pct: float
    match_date_window_days: int


class MatchingRulesUpdate(BaseModel):
    match_auto_accept_confidence: Decimal = Field(ge=0, le=1)
    match_amount_tolerance_pct: Decimal = Field(ge=0)
    match_date_window_days: int = Field(ge=0)


class TaxRuleResponse(BaseModel):
    jurisdiction: str
    label: str
    status: str
    confidence: float


class TaxRulesResponse(BaseModel):
    rules: list[TaxRuleResponse]


class TaxRulesUpdate(BaseModel):
    rules: list[TaxRuleResponse]


class ForecastScenarioRequest(BaseModel):
    opex_delta_pct: Decimal = Decimal("0")
    ar_velocity_delta_pct: Decimal = Decimal("0")


class UploadResponse(BaseModel):
    filename: str
    source: str
    inserted: int


class AccuracyResponse(BaseModel):
    precision: float
    recall: float
    f1: float
    tp: int
    fp: int
    fn: int
    tn: int


class ExportRequest(BaseModel):
    report_type: str = Field(min_length=1)
