/**
 * API contract for Reconcile.io
 *
 * The frontend intentionally reflects the approved contract only.
 * It does not invent extra fields or legacy frontend-only status values.
 */

export type RunStatus = 'running' | 'done';

export interface ReconciliationRunSummary {
  id: string;
  status: RunStatus;
  started_at: string;
  finished_at: string | null;
  records_processed: number;
  match_rate_count: number;
  match_rate_dollar: number;
  auto_matched: number;
  needs_review: number;
  exceptions: number;
}

export interface ReconciliationRunDetail extends ReconciliationRunSummary {
  sources: string[];
  engine_version: string;
}

export interface CreateRunResponse {
  run_id: string;
}

export interface MatchRecord {
  id: string;
  line_a_id: string;
  line_b_id: string;
  tier: number;
  confidence: number;
  variance: number;
  status: string;
}

export type ExceptionStatus = 'new' | 'investigating' | 'resolved' | 'written_off';

export interface ExceptionRecord {
  id: string;
  run_id: string;
  line_id: string;
  reason_code: string;
  reason_text: string;
  status: ExceptionStatus;
  assignee: string | null;
  opened_at: string;
  resolved_at: string | null;
}

export type TaxClassificationStatus = 'auto' | 'review' | 'confirmed' | 'corrected';

export interface TaxClassificationRecord {
  id: string;
  gl_line_id: string;
  jurisdiction: string;
  label: string;
  status: TaxClassificationStatus;
  confidence: number;
  corrected_label: string | null;
}

export interface ForecastSnapshot {
  id: string;
  run_id: string;
  generated_at: string;
  opening_cash: number;
  weeks: Array<{ week: number; projected_cash: number; delta_from_opening: number }>;
  low_point_week: number;
  avg_settlement_lag: number;
}

export interface AuditLogEntry {
  id: string;
  actor: string;
  action: string;
  entity_type: string;
  entity_id: string;
  payload: Record<string, unknown>;
  created_at: string;
}

export interface AccuracyRecord {
  precision: number;
  recall: number;
  f1: number;
  tp: number;
  fp: number;
  fn: number;
  tn: number;
}

export interface CopilotResponse {
  answer: string;
  cited_record_ids: string[];
  mode: string;
}

export interface CopilotHistoryEntry extends CopilotResponse {
  id: string;
  question: string;
  created_at: string;
}

export interface MatchingRules {
  match_auto_accept_confidence: number;
  match_amount_tolerance_pct: number;
  match_date_window_days: number;
}

export interface TaxRule {
  jurisdiction: string;
  label: string;
  status: string;
  confidence: number;
}

export interface RazorpayActivity {
  id: string;
  operation: string;
  status: string;
  response: Record<string, unknown>;
  created_at: string;
}
