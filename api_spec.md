# api_spec.md

Base URL: `http://localhost:8000/api/v1` (local) — live interactive reference always available at `/docs` (Swagger) and `/redoc`; this file is the human-readable summary and must stay in sync with the FastAPI route definitions (checked in CI via an OpenAPI-diff step).

Auth: `Authorization: Bearer <jwt>` on every route except `/webhooks/*` (signature-verified instead) and `/health`.

---

## Ledger
| Method | Path | Purpose |
|---|---|---|
| `POST` | `/ledger/upload` | Upload bank/GL CSV with a column-mapping payload |
| `GET` | `/ledger/lines` | List ledger lines — filters: `source`, `date_from`, `date_to`, `status` |
| `GET` | `/ledger/lines/{id}` | Single line, with raw payload |

## Reconciliation
| Method | Path | Purpose |
|---|---|---|
| `POST` | `/runs` | Trigger a reconciliation run → `202 { run_id }` |
| `GET` | `/runs` | List runs, paginated, newest first |
| `GET` | `/runs/{id}` | Run status + summary metrics (`match_rate_count`, `match_rate_dollar`, `records_processed`) |
| `GET` | `/runs/{id}/matches` | Matches produced by a run — filters: `tier`, `status`, `min_confidence` |
| `POST` | `/matches/{id}/override` | Human override of a match/exception decision — requires `reason`, writes `audit_log` |

**Reason codes** (`exceptions.reason_code`, enumerated — not free text on the machine side, though `reason_text` carries the human-readable detail):
`NO_COUNTERPART` · `STALE_REFERENCE` · `AMOUNT_VARIANCE_EXCEEDS_TOLERANCE` · `DATE_VARIANCE_EXCEEDS_WINDOW` · `IN_TRANSIT_NOT_CLEARED` · `DUPLICATE_CANDIDATE` · `CURRENCY_FX_MISMATCH`

## Exceptions
| Method | Path | Purpose |
|---|---|---|
| `GET` | `/exceptions` | List — filters: `status`, `reason_code`, `assignee`, `source` |
| `PATCH` | `/exceptions/{id}` | Update status/assignee/resolution_note — writes `audit_log` |

## Tax
| Method | Path | Purpose |
|---|---|---|
| `GET` | `/tax/classifications` | List — filters: `jurisdiction`, `status` |
| `PATCH` | `/tax/classifications/{id}` | Confirm or correct a label — correction feeds `golden_labels`-equivalent training set for tax |

## Forecast
| Method | Path | Purpose |
|---|---|---|
| `GET` | `/forecast/latest` | Latest 13-week snapshot |
| `POST` | `/forecast/scenario` | Body: `{ opex_delta_pct, ar_velocity_delta_pct }` → recomputed projection (not persisted, live preview) |

## Copilot
| Method | Path | Purpose |
|---|---|---|
| `POST` | `/copilot/query` | Body: `{ question, mode: "structured" \| "claude" }` → `{ answer, cited_record_ids[] }` |
| `GET` | `/copilot/history` | Past queries for the current user |

## Razorpay
| Method | Path | Purpose |
|---|---|---|
| `POST` | `/razorpay/credentials` | Store test-mode key id/secret (encrypted at rest) |
| `POST` | `/razorpay/test-payment` | Creates a Razorpay test order + simulates payment capture via test card, for live-demo purposes |
| `POST` | `/razorpay/pull-settlements` | On-demand pull from `/settlements` + `/settlements/recon/combined` |
| `POST` | `/webhooks/razorpay` | Webhook receiver — HMAC-verified against `RAZORPAY_WEBHOOK_SECRET` |
| `GET` | `/razorpay/activity` | Recent API calls made by the connector, request/response, for the Live Console's request viewer |

## Accuracy
| Method | Path | Purpose |
|---|---|---|
| `POST` | `/accuracy/benchmark` | Run the engine against `golden_labels`, returns precision/recall/F1 + confusion matrix |
| `GET` | `/accuracy/history` | Metric history across engine versions |
| `GET` | `/accuracy/golden-set` | Browse labeled pairs |

## Audit & export
| Method | Path | Purpose |
|---|---|---|
| `GET` | `/audit` | Filterable audit log |
| `POST` | `/export/pdf` | Body: `{ report_type }` → signed download URL |
| `POST` | `/export/xlsx` | Same shape, XLSX |
| `POST` | `/export/csv` | Same shape, CSV |

## Auth & admin
| Method | Path | Purpose |
|---|---|---|
| `POST` | `/auth/login` | Credentials → JWT |
| `GET` | `/users/me` | Current user + role |
| `GET`/`PATCH` | `/settings/matching-rules` | Tolerance thresholds (amount %, date window, auto-accept confidence) |
| `GET`/`PATCH` | `/settings/tax-rules` | Jurisdiction rule table |

## Example: `GET /runs/{id}`
```json
{
  "id": "run_8f2a...",
  "status": "done",
  "started_at": "2026-09-04T09:00:00Z",
  "finished_at": "2026-09-04T09:00:42Z",
  "records_processed": 61,
  "match_rate_count": 85.2,
  "match_rate_dollar": 84.4,
  "auto_matched": 52,
  "needs_review": 0,
  "exceptions": 9
}
```

## Example: `POST /copilot/query`
```json
// request
{ "question": "what's the biggest open exception?", "mode": "claude" }

// response
{
  "answer": "The largest open exception is [BK-9005] at $14,052.68 — no reference on the bank line and no amount/date/description candidate found in the GL.",
  "cited_record_ids": ["BK-9005"],
  "mode": "claude"
}
```
