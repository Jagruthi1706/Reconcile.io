/**
 * Thin client for the approved API contract.
 *
 * Frontend → FastAPI: http://localhost:8000/api/v1
 */

import type {
  ReconciliationRunSummary,
  ReconciliationRunDetail,
  CreateRunResponse,
  ExceptionRecord,
  TaxClassificationRecord,
  ForecastSnapshot,
  AuditLogEntry,
} from '@/lib/api-types';
import { clearAccessToken, getAccessToken, setAccessToken } from '@/lib/session';

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL ?? '';

class ApiError extends Error {
  status: number;

  constructor(status: number, message: string) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
  }
}

async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const token = getAccessToken();
  const res = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...(init?.headers ?? {}),
    },
  });

  if (!res.ok) {
    if (res.status === 401) {
      clearAccessToken();
      if (typeof window !== 'undefined') window.location.assign('/login');
    }
    throw new ApiError(res.status, `API ${res.status}: ${res.statusText}`);
  }

  if (res.status === 204) {
    return undefined as T;
  }

  return res.json() as Promise<T>;
}

export async function login(email: string, password: string): Promise<void> {
  const res = await fetch(`${API_BASE}/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password }),
  });
  if (!res.ok) throw new ApiError(res.status, 'Unable to sign in');
  const data = await res.json() as { access_token: string };
  setAccessToken(data.access_token);
}

export function logout(): void {
  clearAccessToken();
  if (typeof window !== 'undefined') window.location.assign('/login');
}

export async function getRuns(): Promise<ReconciliationRunSummary[]> {
  return apiFetch<ReconciliationRunSummary[]>('/runs');
}

export async function getRunDetail(runId: string): Promise<ReconciliationRunDetail> {
  return apiFetch<ReconciliationRunDetail>(`/runs/${runId}`);
}

export async function createRun(): Promise<CreateRunResponse> {
  return apiFetch<CreateRunResponse>('/runs', { method: 'POST' });
}

export async function getExceptions(
  params?: { status?: string; reason_code?: string; source?: string }
): Promise<ExceptionRecord[]> {
  const search = new URLSearchParams();
  if (params?.status) search.set('status', params.status);
  if (params?.reason_code) search.set('reason_code', params.reason_code);
  if (params?.source) search.set('source', params.source);
  const qs = search.toString();
  return apiFetch<ExceptionRecord[]>(`/exceptions${qs ? `?${qs}` : ''}`);
}

export async function getTaxClassifications(
  params?: { jurisdiction?: string; status?: string }
): Promise<TaxClassificationRecord[]> {
  const search = new URLSearchParams();
  if (params?.jurisdiction) search.set('jurisdiction', params.jurisdiction);
  if (params?.status) search.set('status', params.status);
  const qs = search.toString();
  return apiFetch<TaxClassificationRecord[]>(`/tax/classifications${qs ? `?${qs}` : ''}`);
}

export async function getLatestForecast(): Promise<ForecastSnapshot> {
  return apiFetch<ForecastSnapshot>('/forecast/latest');
}

export async function getAudit(params?: { limit?: number }): Promise<AuditLogEntry[]> {
  const search = new URLSearchParams();
  if (params?.limit) search.set('limit', String(params.limit));
  const qs = search.toString();
  return apiFetch<AuditLogEntry[]>(`/audit${qs ? `?${qs}` : ''}`);
}
