# AI Finance Controller — Tech Stack & UX Blueprint
*Decision record, written before the doc set (project.spec.md, architecture.md, etc.) so those files inherit settled decisions instead of re-litigating them.*

---

## 1. Tech stack — decided, with rationale

| Layer | Choice | Why this, not the alternative |
|---|---|---|
| Frontend framework | **Next.js 14 (App Router) + TypeScript** | Server components for data-heavy dashboards without a client-side waterfall; file-based routing maps 1:1 to the page list in §4; Vercel deploy is a one-click judge-facing URL. |
| UI system | **Tailwind CSS + shadcn/ui (Radix primitives)** | Accessible-by-default primitives (dialogs, drawers, tables) without a heavy design-system dependency; every component is copied into the repo, so the ledger aesthetic (§4) can be fully overridden rather than fighting a third-party theme. |
| Charts | **Recharts** (line/bar/area/waterfall) + **visx** (calendar heatmap, confusion matrix grid) | Recharts covers 90% of the dashboard needs with low code; visx is used only where Recharts can't (heatmaps), kept isolated to two components. |
| Tables | **TanStack Table v8** | Virtualized rendering for 1,000+ row reconciliation grids; headless so it can wear the ledger styling. |
| Server/client state | **TanStack Query** (server) + **Zustand** (UI state: filters, drawer open/close) | Keeps cache invalidation (a new reconciliation run) simple; avoids Redux boilerplate. |
| Auth | **Auth.js (NextAuth)**, credentials + role claims (`controller`, `analyst`, `auditor-viewer`) | Judges get a read-only `auditor-viewer` demo login that can't mutate data — safe for public evaluation. |
| Backend framework | **FastAPI (Python 3.11)** | The reconciliation/tax/forecast engines are Python (pandas/numpy) already — FastAPI keeps engine and API in one language, gives free OpenAPI docs (doubles as live `api_spec.md`), and is async-native for the Razorpay webhook + polling load. |
| ORM / migrations | **SQLAlchemy 2.0 (async) + Alembic** | Financial data demands versioned, reversible schema migrations — never hand-edit prod schema. |
| Database | **PostgreSQL 15** | ACID transactions for ledger writes; JSONB columns hold raw source payloads (Razorpay webhook bodies) alongside normalized columns — best of both without a second database. |
| Cache / queue broker | **Redis 7** | Celery broker + result cache for the "Run Reconciliation" button's live progress bar. |
| Background jobs | **Celery + Redis** | Ingestion polling, webhook processing, scheduled forecast recompute, and benchmark runs all need to run off the request thread. |
| Reconciliation engine | **Deterministic Python module** (tiers 1–3 as already proven) + **Tier 4 embedding fallback** | Keep the auditable, reproducible core from the prototype; add a semantic-similarity tier (small embedding model, cosine similarity on description text) *only* as a last resort before something becomes an exception — this is the main lever to push match rate past 85%. |
| AI/LLM layer | **Anthropic Claude API** (model configurable, default `claude-sonnet-4-6`), used **only** for: Settlement Copilot phrasing, exception root-cause narratives, and assisting the tax "Unclassified" queue | Never used to *decide* a match — it explains and drafts, always grounded in structured facts it must cite by record ID. This keeps the accuracy number attributable to code, not a model's mood. |
| Accuracy harness | **scikit-learn** (precision/recall/F1, confusion matrix) over a hand-labeled golden set | Turns "85% match rate" into a real, regression-tested metric — see §3.7. |
| PDF/XLSX export | **WeasyPrint** (PDF) + **openpyxl** (XLSX), generated server-side | Keeps export formatting out of the browser; one code path for the "Export Center" and any scheduled board report. |
| Payments/settlement source of truth | **Razorpay Test Mode API** (Orders, Payments, Refunds, Settlements, Settlement Recon Combined report, Webhooks) | Confirmed live endpoints: `/v1/orders`, `/v1/payments`, `/v1/refunds`, `/v1/settlements`, `/v1/settlements/recon/combined` (transaction-level payment↔settlement↔fee↔tax↔UTR mapping — this *is* the reconciliation ground truth), plus `payment.captured` / `settlement.processed` webhooks. Test keys (`rzp_test_...`) generate synthetic-but-real payment flows so the demo is a live API integration, not a mock. |
| Containerization | **Docker Compose** (frontend, backend, worker, postgres, redis, one `docker compose up`) | Single command for a judge or teammate to run the full stack locally. |
| CI | **GitHub Actions** — lint (ruff, eslint), type-check (mypy, tsc), pytest + vitest, Playwright e2e, and the accuracy-benchmark job on every PR that touches the engine | Accuracy regressions block merge, not just data-quality bugs. |
| Deploy targets | Frontend → **Vercel**; backend + worker → **Railway or Fly.io**; DB → managed Postgres (Railway/Neon) | Free-tier-friendly for a competition build; swappable for the same Docker images in production. |

### 1.1 Prerequisites
- Node.js 20+, pnpm 9+
- Python 3.11+, `uv` (or Poetry) for dependency management
- Docker Desktop / Docker Engine + Compose v2
- PostgreSQL 15 and Redis 7 (via Docker, no local install needed)
- Razorpay test account → `RAZORPAY_KEY_ID`, `RAZORPAY_KEY_SECRET`, `RAZORPAY_WEBHOOK_SECRET`
- Anthropic API key → `ANTHROPIC_API_KEY` (optional — Copilot page degrades to structured-answers-only without it, app never breaks)
- `make` or `just` for one-command bootstrap (`make dev`, `make seed`, `make test`, `make bench`)

### 1.2 Pipelines
1. **Ingestion** — Razorpay connector (REST pull + webhook listener) + CSV upload (bank statement, GL export) → normalized into `ledger_lines`, raw payload kept in JSONB for audit.
2. **Matching** — Celery task, tiers 1–4, writes `matches` + `exceptions`, every run versioned (`run_id`) so history is never overwritten.
3. **Tax classification** — runs after matching on GL/opex lines, confidence-gated auto-route.
4. **Forecast** — nightly scheduled + on-demand, recalibrated from the latest run's observed settlement lag.
5. **Copilot (Q&A)** — synchronous, retrieval over Postgres (SQL, not vector search — the ledger is structured, not prose) then Claude formats the answer with mandatory citations.
6. **Export** — on-demand PDF/XLSX/CSV generation for audit and board reporting.
7. **Accuracy benchmark** — runs the engine against a labeled golden set, stores metric history; triggerable from CI or the Accuracy page.

### 1.3 Engines (five, one shared audit trail)
1. **Reconciliation Engine** — deterministic tiers 1–3 + embedding-based tier 4.
2. **Tax Engine** — rule table + confidence threshold, editable from Settings.
3. **Forecast Engine** — aging/collection-curve model, self-calibrating.
4. **Copilot Engine** — Claude-backed, citation-enforced, structured-fact-grounded.
5. **Accuracy/Eval Engine** — precision/recall/F1 + confusion matrix, the thing that proves the other four aren't cherry-picked.

---

## 2. Accuracy, precisely (not just "match rate")

"85% is great, we'll increase it" — to make that measurable instead of vibes-based:
- **Golden dataset**: a hand-labeled batch (Razorpay test payments + matching bank/GL lines, seeded via `make seed`) where the *correct* match is known in advance.
- **Metrics tracked**: precision, recall, F1, plus a confusion matrix with four cells — correct match, **missed match** (should've matched, called an exception — the dangerous one), **false match** (matched wrong pair — the *very* dangerous one), correct exception.
- **Every engine change re-runs the benchmark in CI** — the Accuracy page (§4.8) plots the trend so the improvement from 85%→higher is a visible, versioned line, not a claim.

---

## 3. UI/UX — page by page

**Visual identity** carries forward from the prototype dashboard: ink (`#141F1A`) shell, parchment (`#F4EFE2`) data panels, tabular monospace figures, serif headings — a ledger, not a generic SaaS kit. This is a deliberate choice for a finance product being judged: it reads as *earned* authority rather than a templated dashboard, and it's distinctive enough that a jury remembers it after seeing twenty other Tailwind-default entries.

**Global shell**: left sidebar (icons + labels, collapsible), top bar with a `TEST MODE` badge (always visible — never let anyone mistake this for touching real money), a global record-ID search, and a `⌘K` command palette so a judge can jump straight to any page or record without hunting through nav.

| # | Page | Route | Purpose & key components |
|---|---|---|---|
| 0 | **Pitch / Landing** | `/pitch` | The 30-second version for a judge who opens the link cold: hero stat (live match rate, pulled from the DB, not hardcoded), one-paragraph explanation, architecture strip (the five-node diagram from the prototype), a "Launch live console" CTA straight into `/razorpay`. No login required. |
| 1 | **Overview / Command Center** | `/` | KPI band (match rate count/$, open exceptions, cash low-point, tax review queue) · 13-week cash sparkline · **exceptions-by-source calendar heatmap** (day × source, colored by density) · live activity feed · "Run Reconciliation Now" button with a progress toast. |
| 2 | **Reconciliation Workbench** | `/reconcile` | Virtualized TanStack table of every ledger line, filterable by source/tier/confidence/status/date · tier-distribution bar chart pinned above the table · click a row → side drawer with the matched pair rendered side-by-side, diffed field-by-field · bulk approve/override with a reason field (feeds the audit trail). |
| 3 | **Exception Explorer** | `/exceptions` | Kanban (New → Investigating → Resolved → Written-off) with a table-view toggle · root-cause tag filter chips · **aging heatmap** (days-open × reason-code) so a stale, high-value exception is visually impossible to miss · assign + resolution-note workflow, every action timestamped. |
| 4 | **Tax-Line Matcher** | `/tax` | Jurisdiction breakdown bars (as prototyped) · confidence-distribution histogram · review queue table with inline confirm/correct — a correction is captured as a labeled example for the next accuracy benchmark. |
| 5 | **Cash Forecast** | `/forecast` | 13-week line chart with a shaded confidence band · scenario sliders (best/base/worst opex & AR velocity) recompute live · weekly inflow/outflow **waterfall chart** · low-point alert card · calibration panel showing the settlement-lag input pulled from the latest reconciliation run. |
| 6 | **Settlement Copilot** | `/copilot` | Chat UI grounded in the ledger · suggested-prompt chips · every answer's cited record IDs render as clickable chips deep-linking into the Workbench drawer · visible toggle between "structured-only" and "Claude-enhanced" so the AI's exact contribution is never hidden. |
| 7 | **Razorpay Live Test Console** | `/razorpay` | Connect test keys · "Generate test payment" and "Pull settlements" buttons that hit the real Razorpay test API · live request/response viewer · triggers a real reconciliation run on real (test-mode) data and shows the before/after match-rate delta on screen — this is the page that proves the product against Razorpay live, for a judge watching in real time. |
| 8 | **Accuracy & Evaluation** | `/accuracy` | Precision/recall/F1 trend line across engine versions · **confusion-matrix heatmap** (matched / missed / false-match / false-exception) · golden-dataset browser · "Run Benchmark" button. |
| 9 | **Audit Trail & Export Center** | `/audit` | Immutable, filterable event log · one-click export to PDF (board report), XLSX (raw ledger), CSV (exceptions), each with a preview before download. |
| 10 | **Settings / Admin** | `/settings` | Razorpay key management, bank-CSV column mapping, matching-tolerance rule editor, tax rule table editor, user roles. |

Table, heatmap, bar, line, waterfall, and confusion-matrix visuals are each used exactly where they answer a specific question (not decoratively) — match quality over time → line; where exceptions cluster → heatmap; what makes up cash flow → waterfall; is the engine improving or guessing → confusion matrix.

---

## 4. What's next
This blueprint is the input to the doc set. Once you confirm or adjust anything above, I'll produce `project.spec.md`, `architecture.md`, `agent.md`, `decisions.md`, `api_spec.md`, `environment.md`, `testing.md`, `tasks.md`, `roadmap.md`, and `readme.md` against these exact decisions — so nothing in the docs contradicts what's written here.
