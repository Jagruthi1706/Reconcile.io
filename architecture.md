# architecture.md

## 1. System overview

```
                         ┌─────────────────────────────────────────┐
                         │              apps/web (Next.js)          │
                         │  Overview · Reconcile · Exceptions ·     │
                         │  Tax · Forecast · Copilot · Razorpay ·   │
                         │  Accuracy · Audit · Settings              │
                         └───────────────┬───────────────────────────┘
                                         │ REST (OpenAPI) + polling
                         ┌───────────────▼───────────────────────────┐
                         │              apps/api (FastAPI)            │
                         │  routers/  · auth · rate limit · webhooks  │
                         └───┬─────────────────┬─────────────────┬───┘
                             │                 │                 │
                 ┌───────────▼──────┐ ┌────────▼───────┐ ┌───────▼────────┐
                 │  packages/engine  │ │  Celery worker  │ │  Claude (API)   │
                 │  reconciliation   │ │  scheduled +    │ │  Copilot only — │
                 │  tax · forecast   │ │  triggered jobs │ │  read-only tools│
                 │  accuracy         │ └────────┬────────┘ └────────┬────────┘
                 └─────────┬─────────┘          │                   │
                           │           ┌─────────▼─────────┐         │
                           │           │   Redis (broker/   │         │
                           │           │   cache)            │         │
                           │           └─────────────────────┘         │
                 ┌─────────▼─────────────────────────────────────────▼───┐
                 │                     PostgreSQL 15                      │
                 │  ledger_lines · matches · exceptions · runs · tax ·    │
                 │  forecast_snapshots · golden_labels · benchmarks ·     │
                 │  audit_log · users · razorpay_credentials              │
                 └───────────┬──────────────────────────────────────────┘
                             │
             ┌───────────────▼───────────────────┐
             │   Razorpay Test Mode API + Webhooks │
             │  Orders · Payments · Refunds ·      │
             │  Settlements · /settlements/recon/  │
             │  combined                            │
             └───────────────────────────────────────┘
```

**Design rule enforced by this architecture**: only `packages/engine` decides whether two lines match. The API layer orchestrates and persists; the frontend renders; Claude explains. No component upstream of the engine can silently change a match result.

## 2. Data flow — end to end
1. **Ingest** — Razorpay connector pulls Orders/Payments/Settlements/Recon on a schedule and via webhook; CSV upload path normalizes bank/GL files using a saved column mapping. Both paths write to `ledger_lines`, raw payload preserved in `raw_payload JSONB`.
2. **Match** — a `reconciliation_runs` row is created; the engine runs tiers 1–4 over unmatched `ledger_lines`; writes to `matches` (matched pairs) and `exceptions` (unresolved, with `reason_code`).
3. **Classify** — tax engine runs over new/changed GL lines, writes `tax_classifications`.
4. **Forecast** — forecast engine reads the latest run's settlement-lag statistic, recomputes `forecast_snapshots`.
5. **Serve** — frontend polls `reconciliation_runs.status`, renders from the four tables above plus `audit_log`.
6. **Explain** — Copilot queries route through a retrieval step (parameterized SQL against the same tables) before any Claude call; Claude receives only the retrieved rows as context and a system prompt that requires citing `id`s present in that context.
7. **Benchmark** — accuracy engine runs the same tier 1–4 matcher against `golden_labels`, writes `accuracy_benchmarks`.

## 3. Database schema (core tables)

```sql
ledger_lines (
  id UUID PK, source TEXT,            -- bank | gl | razorpay_payment | razorpay_settlement | invoice
  external_ref TEXT, amount NUMERIC(14,2), currency TEXT,
  description TEXT, txn_date DATE, entity TEXT,
  raw_payload JSONB, created_at TIMESTAMPTZ
)

reconciliation_runs (
  id UUID PK, started_at TIMESTAMPTZ, finished_at TIMESTAMPTZ,
  records_processed INT, match_rate_count NUMERIC(5,2), match_rate_dollar NUMERIC(5,2),
  triggered_by TEXT                    -- schedule | manual | webhook
)

matches (
  id UUID PK, run_id UUID FK, line_a_id UUID FK, line_b_id UUID FK,
  tier INT, confidence NUMERIC(4,3), variance NUMERIC(14,2),
  status TEXT,                         -- auto-matched | needs-review | overridden
  created_at TIMESTAMPTZ
)

exceptions (
  id UUID PK, run_id UUID FK, line_id UUID FK,
  reason_code TEXT, reason_text TEXT,
  status TEXT,                         -- new | investigating | resolved | written_off
  assignee TEXT, resolution_note TEXT,
  opened_at TIMESTAMPTZ, resolved_at TIMESTAMPTZ
)

tax_classifications (
  id UUID PK, gl_line_id UUID FK, jurisdiction TEXT, label TEXT,
  confidence NUMERIC(4,3), status TEXT, -- auto | review | confirmed | corrected
  corrected_label TEXT
)

forecast_snapshots (
  id UUID PK, run_id UUID FK, generated_at TIMESTAMPTZ,
  opening_cash NUMERIC(14,2), weeks JSONB,
  low_point_week INT, avg_settlement_lag NUMERIC(5,2)
)

golden_labels (
  id UUID PK, line_a_id UUID FK, line_b_id UUID FK,
  expected_match BOOLEAN, notes TEXT
)

accuracy_benchmarks (
  id UUID PK, engine_version TEXT, run_at TIMESTAMPTZ,
  precision NUMERIC(4,3), recall NUMERIC(4,3), f1 NUMERIC(4,3),
  tp INT, fp INT, fn INT, tn INT
)

copilot_queries (
  id UUID PK, user_id UUID FK, question TEXT, answer TEXT,
  cited_record_ids JSONB, mode TEXT,   -- structured | claude
  created_at TIMESTAMPTZ
)

audit_log (
  id UUID PK, actor TEXT, action TEXT, entity_type TEXT, entity_id UUID,
  payload JSONB, created_at TIMESTAMPTZ
)

users (id UUID PK, email TEXT, role TEXT, created_at TIMESTAMPTZ)

razorpay_credentials (
  id UUID PK, key_id TEXT, key_secret_encrypted TEXT,
  webhook_secret_encrypted TEXT, mode TEXT, connected_at TIMESTAMPTZ
)
```

## 4. Sequence: manual reconciliation run
```
User → web: click "Run Reconciliation Now"
web → api: POST /runs
api → db: INSERT reconciliation_runs (status=running)
api → celery: enqueue match_task(run_id)
api → web: 202 { run_id }
web → api: poll GET /runs/{id} every 1.5s
celery → engine: tiers 1-4 over unmatched ledger_lines
engine → db: INSERT matches, exceptions
celery → tax engine → db: INSERT tax_classifications
celery → forecast engine → db: INSERT forecast_snapshots
celery → db: UPDATE reconciliation_runs (status=done, match_rate_*)
web → api: GET /runs/{id} → status=done
web: renders updated KPI band + tables
```

## 5. Sequence: Razorpay webhook
```
Razorpay → api: POST /webhooks/razorpay (payload + X-Razorpay-Signature)
api: verify HMAC signature against RAZORPAY_WEBHOOK_SECRET → reject if invalid
api → db: INSERT ledger_lines (source=razorpay_payment/settlement, raw_payload=body)
api → celery: enqueue incremental match_task (scoped to new lines)
api → 200 OK (fast ack, processing is async)
```

## 6. Sequence: Copilot query
```
User → web: "why is PO-014 short by ₹210?"
web → api: POST /copilot/query
api: parse for record IDs / intent → build SQL retrieval (bounded, parameterized)
api → db: fetch matched rows for PO-014 + any linked exceptions
api → claude: system prompt (cite-or-refuse) + retrieved rows as context + question
claude → api: draft answer with [record_id] citations
api: validate every cited id exists in the retrieved context → strip/flag any that don't
api → db: INSERT copilot_queries (for audit)
api → web: answer + clickable citation chips
```

## 7. Deployment topology
- `docker-compose.yml` (local/dev): `web`, `api`, `worker`, `postgres`, `redis` — one command, no external dependency except live Razorpay/Anthropic API calls if keys are set.
- Production: `web` → Vercel; `api` + `worker` → Railway/Fly.io (same Docker image, different `CMD`); `postgres`/`redis` → managed instances. No infrastructure divergence between environments beyond connection strings.
