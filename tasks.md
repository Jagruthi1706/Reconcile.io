# tasks.md

Organized by epic. Each epic is independently demoable where possible, so partial progress still shows well.

## Epic 0 — Infra bootstrap
- [ ] Monorepo scaffold (`apps/web`, `apps/api`, `packages/engine`, `infra/`, `data/`)
- [ ] `docker-compose.yml` with all 5 services
- [ ] `.env.example` + hard guard rejecting non-`test` `RAZORPAY_MODE`
- [ ] GitHub Actions skeleton: lint + type-check jobs green on an empty diff
- [ ] `Makefile`/`justfile`: `dev`, `migrate`, `seed`, `bench`, `test`

## Epic 1 — Data model & migrations
- [ ] Alembic setup, initial migration for all core tables (§3 of `architecture.md`)
- [ ] SQLAlchemy models + Pydantic schemas mirrored 1:1
- [ ] Seed script for demo data (`data/seed/`)
- [ ] Golden-label seed script (`data/golden/`), 30 initial labeled pairs to unblock CI

## Epic 2 — Ingestion connectors
- [ ] Razorpay client (`httpx`, async): Orders, Payments, Refunds, Settlements
- [ ] Recon-combined puller + fallback composition path (ADR-005)
- [ ] Webhook receiver + HMAC verification + fixture-based contract tests
- [ ] CSV upload endpoint + column-mapping UI stub
- [ ] Normalize-to-`ledger_lines` shared function used by both paths

## Epic 3 — Reconciliation engine
- [ ] Port tiers 1–3 from the prototype into `packages/engine/reconciliation.py`, fully unit tested
- [ ] Add tier 4 (embedding similarity), hard-capped confidence, review-only
- [ ] Reason-code classifier for non-matches
- [ ] `reconciliation_runs` orchestration + Celery task
- [ ] Match-rate calculation (count + dollar-weighted)

## Epic 4 — Tax engine
- [ ] Rule table (jurisdiction, pattern, label, confidence) — editable, seeded with the prototype's ruleset
- [ ] Confidence-gated auto-classify vs. review-queue routing
- [ ] Correction → labeled example capture

## Epic 5 — Forecast engine
- [ ] Aging/collection-curve model ported from prototype
- [ ] Calibration from latest run's settlement lag
- [ ] Scenario recompute endpoint (best/base/worst)

## Epic 6 — Copilot
- [ ] Read-only tool set (`get_record`, `get_exceptions`, `get_match_rate`, `get_forecast`, `get_tax_summary`)
- [ ] Retrieval-before-generation query flow
- [ ] Citation-verification pass + fallback-to-structured on repeated failure
- [ ] Structured-only mode (works without `ANTHROPIC_API_KEY`)

## Epic 7 — Accuracy harness
- [ ] `bench.py`: precision/recall/F1/confusion matrix over `golden_labels`
- [ ] `accuracy_benchmarks` persistence + history endpoint
- [ ] CI gate: F1 regression >2pts or any false-match increase fails the build
- [ ] Grow golden set to 150+ labeled pairs, ≥5 examples per reason code

## Epic 8 — Frontend shell + pages
- [ ] Design tokens (ledger palette/type) as a Tailwind config, not per-component overrides
- [ ] App shell: sidebar, top bar, `TEST MODE` badge, `⌘K` command palette
- [ ] Page: Pitch/Landing
- [ ] Page: Overview/Command Center (KPI band, cash sparkline, exceptions heatmap)
- [ ] Page: Reconciliation Workbench (virtualized table, drawer diff view)
- [ ] Page: Exception Explorer (Kanban + table toggle, aging heatmap)
- [ ] Page: Tax-Line Matcher
- [ ] Page: Cash Forecast (scenario sliders, waterfall)
- [ ] Page: Settlement Copilot (chat UI, citation chips)
- [ ] Page: Razorpay Live Test Console
- [ ] Page: Accuracy & Evaluation (confusion-matrix heatmap, trend line)
- [ ] Page: Audit Trail & Export Center
- [ ] Page: Settings/Admin

## Epic 9 — Export center
- [ ] PDF board report (WeasyPrint template)
- [ ] XLSX raw ledger (openpyxl)
- [ ] CSV exceptions
- [ ] Preview-before-download in the UI

## Epic 10 — Auth & roles
- [ ] Auth.js credentials provider + JWT
- [ ] Roles: `controller`, `analyst`, `auditor-viewer`
- [ ] Write-endpoint role guard, verified by direct API test (not just hidden UI) — see `testing.md` §5

## Epic 11 — Testing & CI gates
- [ ] Unit + integration suites for every engine and route
- [ ] Playwright specs for all 11 pages (§4 of `testing.md`)
- [ ] Full CI pipeline: lint → type-check → unit → integration → bench → e2e

## Epic 12 — Demo polish & deployment
- [ ] Deploy `web` to Vercel, `api`/`worker` to Railway/Fly.io, managed Postgres/Redis
- [ ] Seeded demo environment with a stable public URL
- [ ] Dry-run the full judge path: land on `/pitch` → live console → accuracy page → export, timed under 5 minutes
- [ ] README quickstart verified on a clean machine by someone who didn't write the code
