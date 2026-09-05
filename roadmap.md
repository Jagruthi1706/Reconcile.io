# roadmap.md

A 2-week build plan (adjust to your actual deadline — the phase *order* and dependencies matter more than the exact day count).

## Phase 0 — Foundation (Days 1–2)
**Goal**: everything boots, nothing is built yet.
- Epic 0 (infra bootstrap) complete
- Epic 1 (data model) complete
- `make dev && make seed` works on a clean machine
- **Milestone**: empty app, real database, real Docker Compose, CI green on an empty diff

## Phase 1 — Core engine, headless (Days 3–5)
**Goal**: the reconciliation/tax/forecast engines are correct and tested before any UI exists.
- Epic 2 (ingestion) — Razorpay connector + CSV upload
- Epic 3 (reconciliation engine) — tiers 1–4
- Epic 4 (tax engine)
- Epic 5 (forecast engine)
- Epic 7 (accuracy harness) — first golden set, first benchmark number
- **Milestone**: `make bench` prints a real precision/recall/F1 against real Razorpay test-mode data pulled through the actual connector — the hard part is done before a single page is styled

## Phase 2 — Frontend core (Days 6–8)
**Goal**: the story is visible.
- Epic 8, pages: Pitch/Landing, Overview, Reconciliation Workbench, Exception Explorer, Tax-Line Matcher, Cash Forecast
- Epic 10 (auth & roles) — enough to gate write actions
- **Milestone**: a judge can click through five pages and understand the product without narration

## Phase 3 — Copilot + live console (Days 9–10)
**Goal**: the two "wow" pages.
- Epic 6 (Copilot) — structured mode first, Claude-enhanced mode second
- Epic 8, pages: Settlement Copilot, Razorpay Live Test Console
- **Milestone**: generate a real test payment on Razorpay, pull its settlement, watch the match-rate number move, live, on screen

## Phase 4 — Accuracy push + audit/export (Days 11–12)
**Goal**: prove the number, don't just show it.
- Epic 7 continued — grow golden set to 150+, tune tier-4 thresholds to push F1 up from the Phase 1 baseline
- Epic 8, pages: Accuracy & Evaluation, Audit Trail & Export Center, Settings
- Epic 9 (export center)
- **Milestone**: the Accuracy page shows a visible upward trend line across at least 3 benchmark runs — the "we'll increase it while building" claim, proven

## Phase 5 — Hardening & demo rehearsal (Days 13–14)
**Goal**: nothing embarrassing happens live.
- Epic 11 (full test suite + CI gates)
- Epic 12 (deploy + demo dry run)
- Manual QA checklist in `testing.md` §5, fully checked
- **Milestone**: full judge-path walkthrough, timed, on the deployed URL, by someone other than the builder

## Later (post-v1, not blocking the current build)
- Real bank connectivity (Plaid / account-aggregator) instead of CSV upload
- Multi-entity/multi-currency consolidation
- Multi-tenant workspace support
- Live-mode Razorpay support, behind an explicit, audited opt-in
- Additional processor connectors (Stripe, PayU) using the same canonical `ledger_lines` schema — the ingestion layer was designed for this from Epic 2 on
