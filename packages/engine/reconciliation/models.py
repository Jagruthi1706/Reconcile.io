from dataclasses import dataclass
from decimal import Decimal
from enum import StrEnum
from uuid import UUID

from packages.engine.reconciliation.reason_codes import ReasonCode


class MatchStatus(StrEnum):
    AUTO_MATCHED = "auto-matched"
    MATCHED_NEEDS_REVIEW = "matched-needs-review"


@dataclass(frozen=True, slots=True)
class MatchDecision:
    left_id: UUID
    right_id: UUID
    tier: int
    confidence: Decimal
    variance: Decimal
    status: MatchStatus


@dataclass(frozen=True, slots=True)
class ExceptionDecision:
    record_id: UUID
    reason_code: ReasonCode
    reason_text: str


@dataclass(frozen=True, slots=True)
class ReconciliationResult:
    matches: tuple[MatchDecision, ...]
    exceptions: tuple[ExceptionDecision, ...]
