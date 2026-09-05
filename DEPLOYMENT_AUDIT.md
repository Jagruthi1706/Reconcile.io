# Deployment Readiness Audit — Reconcile.io v1
**Date**: 2026-09-05  
**Status**: PHASE 5 ENTRY — Core features complete; integration and calibration work required  

---

## Executive Summary

The project has successfully completed all core features (reconciliation engine, data model, API routes, frontend scaffolding, and test infrastructure). **18/18 tests pass.** However, three specific required features are incomplete before deployment:

1. **Settlement lag calibration** — currently hardcoded to 0.00
2. **Razorpay test-payment capture** — creates order but doesn't simulate payment capture
3. **Frontend page completeness** — all pages exist but UI depth/interactions need verification

All other **19 functional requirements (FR-1 through FR-20)** from the specification are implemented and tested. The role matrix and audit trail are in place.

---

## Feature Checklist: Original Requirements vs. Current State

### ✅ DONE — Fully Implemented and Tested

#### Ingestion (FR-1 to FR-4)
- [x] **FR-1**: Razorpay test-mode Orders, Payments, Refunds, Settlements API integration via `api/integrations/razorpay/client.py`
- [x] **FR-2**: Bank/GL CSV upload with column mapping via `/ledger/upload` endpoint
- [x] **FR-3**: Razorpay webhook receiver with HMAC signature verification in `api/webhooks.py`
- [x] **FR-4**: Raw payload preservation in JSONB `LedgerLine.raw_payload` column

#### Reconciliation (FR-5 to FR-8)
- [x] **FR-5**: Four-tier matching engine (exact reference, tolerance-based, description similarity, embedding) in `packages/engine/reconciliation/`
- [x] **FR-6**: Match results carry `tier`, `confidence`, `variance`; non-matches carry `reason_code` (7 codes: NO_COUNTERPART, STALE_REFERENCE, AMOUNT_VARIANCE_EXCEEDS_TOLERANCE, etc.)
- [x] **FR-7**: Match rate calculated both by line count and dollar value in `api/reconciliation/service.py`
- [x] **FR-8**: Versioned reconciliation runs with UUIDs — history never overwritten

#### Tax (FR-9 to FR-10)
- [x] **FR-9**: GL line classification by jurisdiction/treatment/confidence via `api/tax.py` rule engine
- [x] **FR-10**: Confidence-gated routing to review queue; corrections feed `TaxTrainingExample` table

#### Forecast (FR-11, FR-13)
- [x] **FR-11**: 13-week cash projection via `api/forecast.py::project()`
- [x] **FR-13**: Scenario recalculation endpoint `/forecast/scenario` with opex/AR velocity deltas

#### Copilot (FR-14 to FR-15)
- [x] **FR-14**: Natural-language Q&A via Claude/Gemini with structured retrieval (`api/copilot.py`)
- [x] **FR-15**: Citation verification — all cited record IDs validated against context before response returned

#### Accuracy (FR-16 to FR-18)
- [x] **FR-16**: Hand-labeled golden dataset in `data/golden/labels.jsonl`
- [x] **FR-17**: Precision, recall, F1, confusion matrix computed by `packages/engine/bench.py`
- [x] **FR-18**: Benchmark history persisted in `AccuracyBenchmark` table

#### Audit & Export (FR-19 to FR-20)
- [x] **FR-19**: Immutable audit log in `AuditLog` table — every match override and exception update logged with actor/timestamp
- [x] **FR-20**: Export endpoints for PDF (board report), XLSX (ledger), CSV (exceptions) via `api/exports.py`

#### Infrastructure & Auth
- [x] All 12 API endpoint families from `api_spec.md` implemented with correct method/path
- [x] Role-based access control: `controller`, `analyst`, `auditor-viewer` roles (ADR-009)
- [x] Write endpoints protected by `require_write_role()` dependency — **verified in test_v1_features.py**
- [x] Celery + Redis integration for background reconciliation tasks
- [x] Database migrations complete (3 versions: initial schema, auth settings, razorpay activity)
- [x] All 11 frontend pages scaffolded: Pitch, Overview, Reconcile, Exceptions, Tax, Forecast, Copilot, Razorpay, Accuracy, Audit, Settings

---

### 🔴 REQUIRED BEFORE DEPLOYMENT — Incomplete

#### 1. Settlement Lag Calibration (FR-12)
**Requirement**: "The model recalibrates its collection curve using the settlement lag observed in the latest reconciliation run."

**Current State**: Settlement lag is hardcoded to `Decimal("0.00")` in `api/forecast.py::project()`, line 19.

**What's Missing**: 
- Reconciliation runs must calculate and store `avg_settlement_lag` (average days between payment `txn_date` and settlement `txn_date` for matched pairs)
- Forecast endpoint must retrieve latest run's `avg_settlement_lag` and pass to `project()`
- Test coverage for lag calculation

**Files to Change**:
- `api/reconciliation/service.py` — add lag calculation after tiers 1-4 matching
- `api/forecast.py` — use stored lag instead of hardcoded 0.00
- `tests/test_v1_features.py` — add lag calculation test

**Effort**: ~1 hour | **Blocker**: Yes, required by spec FR-12

---

#### 2. Razorpay Test-Payment Flow — Capture Step
**Requirement**: "Creates a Razorpay test order + simulates payment capture via test card, for live-demo purposes" (api_spec.md, section Razorpay).

**Current State**: POST `/razorpay/test-payment` creates an order but does not capture the payment.

**What's Missing**:
- After creating an order, the endpoint must simulate capturing the payment using Razorpay's test-card flow
- Razorpay test-mode API allows test card capture via POST `/payments/pay_id/capture`
- The capture should trigger webhook notification (`payment.captured`), which ingests the payment into `ledger_lines`

**Files to Change**:
- `api/integrations/razorpay/client.py` — add `capture_payment(payment_id)` method
- `api/razorpay.py` — extend `provider_call()` to support two-step create+capture
- Update POST `/razorpay/test-payment` to call capture after order creation
- Add test in `tests/test_v1_features.py`

**Effort**: ~2 hours | **Blocker**: Yes, required for live-demo path (testing.md §4 Razorpay Live Console page)

---

#### 3. Frontend Page Completeness Verification
**Requirement**: All 11 pages must be navigable and fully functional per `tech-stack-and-ux-blueprint.md` §3.

**Current State**: All 11 page directories exist with `page.tsx` files, but UI depth/interactivity needs verification against the specification.

**What to Verify**:
- [ ] Page 0 (Pitch/Landing): Hero stat pulls live number from DB (not placeholder)
- [ ] Page 1 (Overview): KPI band, cash sparkline, exceptions heatmap, "Run Reconciliation Now" button
- [ ] Page 2 (Reconciliation Workbench): Virtualized table, side-drawer diff view, bulk override
- [ ] Page 3 (Exception Explorer): Kanban view, aging heatmap
- [ ] Page 4 (Tax-Line Matcher): Confidence histogram, review queue table
- [ ] Page 5 (Cash Forecast): 13-week chart, scenario sliders, waterfall
- [ ] Page 6 (Settlement Copilot): Chat UI, citation chips
- [ ] Page 7 (Razorpay Live Test Console): "Generate test payment" button, real Razorpay integration test
- [ ] Page 8 (Accuracy & Evaluation): Confusion-matrix heatmap, trend line, "Run Benchmark" button
- [ ] Page 9 (Audit Trail & Export Center): Event log, export buttons
- [ ] Page 10 (Settings/Admin): Razorpay key management, tax rule editor, matching tolerance editor

**Effort**: Pending manual QA walkthrough | **Blocker**: Yes, required for judge evaluation

---

#### 4. Migrations Status
**Requirement**: Alembic migrations must be up-to-date and reversible.

**Current State**: 3 migrations exist (0001_initial_schema, 0002_auth_settings, 0003_razorpay_activity).

**Verification Needed**: Run `alembic heads` to confirm current state and `alembic current` to confirm applied.

**Effort**: ~15 min | **Blocker**: Potentially — if migrations are pending or conflicting

---

### 📋 POST-V1 / OPTIONAL — Explicitly Deferred

- **Claude LLM integration for Copilot** — Currently using Gemini; Claude support is marked as optional in environment.md and deferred in decisions.md
- **Live-mode Razorpay** — Explicitly forbidden; test-mode only enforced by `RAZORPAY_MODE` check in `RazorpayClient.__post_init__`
- **Multi-currency consolidation** — CSV-upload accepts multi-currency, but no FX conversion logic (noted in roadmap.md "Later")
- **Real bank connectivity** — Plaid/account-aggregator deferred; CSV upload sufficient for v1
- **Multi-tenant workspace** — Single organization per deployment in v1

---

## Implementation Plan: Required Items (Vertical Slices)

### Slice 1: Settlement Lag Calibration (1 hour)
**Goal**: FR-12 complete — forecast recalibrates from observed settlement lag.

1. Add `avg_settlement_lag` calculation in `api/reconciliation/service.py::run_reconciliation()`
2. Update `api/forecast.py` to use stored lag
3. Add unit test for lag calculation
4. Run `pytest -q` to confirm

**Files Changed**: `api/reconciliation/service.py`, `api/forecast.py`, `tests/test_v1_features.py`

---

### Slice 2: Razorpay Test-Payment Capture Flow (2 hours)
**Goal**: `/razorpay/test-payment` creates order and captures payment end-to-end.

1. Add `capture_payment()` method to `RazorpayClient`
2. Update `POST /razorpay/test-payment` endpoint to capture after order creation
3. Ensure capture triggers webhook → ingests payment into ledger
4. Add integration test
5. Run `pytest -q` and manual e2e test via `/razorpay` page

**Files Changed**: `api/integrations/razorpay/client.py`, `api/razorpay.py`, `api/main.py`, tests

---

### Slice 3: Frontend Page Verification (2 hours)
**Goal**: All 11 pages fully functional and UI-complete.

1. Review each page against `tech-stack-and-ux-blueprint.md` §3
2. Verify charts render (Recharts, visx), tables virtualize, forms submit
3. Check API integration (TanStack Query, Zustand state)
4. Fix any missing functionality or styling
5. Run `pnpm build && pnpm lint && pnpm typecheck`

**Files Changed**: `apps/web/app/**/page.tsx`, `apps/web/components/*`

---

## Validation & Testing

### Backend
```bash
python -m compileall -q api
pytest -q
pytest -q tests/test_v1_features.py api/integrations/razorpay/tests
alembic heads
```

### Frontend
```bash
cd apps/web
pnpm typecheck
pnpm build
pnpm lint
```

### Route Audit (Duplicate Prevention)
Run FastAPI `/docs` to verify no duplicate method/path combinations.

---

## Deployment Readiness Checklist

| Item | Status | Notes |
|---|---|---|
| **Code Compilation** | 🟡 Pending | Need to run `python -m compileall -q api` |
| **Python Tests** | ✅ 18/18 pass | `pytest -q` shows all passing |
| **API Routes** | ✅ Spec-complete | 40+ routes implemented, role matrix verified |
| **Razorpay Integration** | 🔴 Incomplete | Test-payment must include capture |
| **Settlement Lag** | 🔴 Incomplete | Hardcoded 0.00, must be calculated |
| **Frontend Typecheck** | 🟡 Pending | Need `pnpm typecheck` |
| **Frontend Build** | 🟡 Pending | Need `pnpm build` |
| **Frontend Lint** | 🟡 Pending | Need `pnpm lint` |
| **Migrations Current** | 🟡 Pending | Need `alembic current` and `alembic heads` |
| **Live Data Testing** | 🟡 Pending | Requires Railway PostgreSQL, Redis, Razorpay test account |
| **E2E Path (Judge)** | 🟡 Pending | Manual walkthrough of landing → console → accuracy → export |
| **Role Matrix Audit** | ✅ Complete | Test verifies all write endpoints protected |
| **Citation Verification** | ✅ Complete | Copilot implements cite-or-refuse pattern |
| **Audit Trail** | ✅ Complete | Every action logged with actor/timestamp |

---

## Deployment Blockers

### Code-Level Blockers
1. **Settlement lag hardcoded** — Will cause incorrect forecast numbers; must fix before deploy
2. **Test-payment endpoint incomplete** — Cannot demo live Razorpay integration; must fix before judge sees it
3. **Frontend pages untested** — Cannot verify UI/UX works end-to-end; must complete and QA before deploy

### External Blockers (Requiring External Services)
1. **Railway PostgreSQL connection** — Needed for prod data validation
2. **Railway Redis connection** — Needed for Celery worker testing in prod
3. **Razorpay test account** — Already assumed to be set up (RAZORPAY_KEY_ID/SECRET in .env)
4. **Vercel deployment** — Not yet attempted; may have config issues
5. **GitHub → Railway → Vercel pipeline** — CI/CD not yet tested end-to-end

---

## Code Freeze Readiness

**NOT READY** — Three required items must be implemented first:
1. Settlement lag calibration
2. Test-payment capture
3. Frontend page QA verification

**Expected readiness**: After 3–4 hours of implementation + testing

---

## Exact Next Steps (If Ready to Deploy)

Once all three blockers above are resolved and tests pass:

1. **GitHub Push**:
   ```bash
   git add -A && git commit -m "Deployment v1: settlement-lag + test-payment + frontend QA"
   git push origin main
   ```

2. **Railway API Deploy**:
   - Connect Railway project to GitHub
   - Set environment variables (DATABASE_URL, REDIS_URL, RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET, RAZORPAY_WEBHOOK_SECRET)
   - Trigger deploy from Railway dashboard

3. **Railway Worker Deploy**:
   - Same Docker image, different `CMD celery worker`
   - Verify in Railway logs that worker connects to Redis

4. **Vercel Frontend Deploy**:
   - Connect Vercel project to GitHub
   - Set environment variables (NEXT_PUBLIC_API_BASE_URL → Railway API URL)
   - Trigger deploy from Vercel dashboard

5. **Razorpay Webhook Configuration**:
   - Update Razorpay dashboard webhook URL to point to Railway API `/api/v1/webhooks/razorpay`
   - Confirm webhook secret matches RAZORPAY_WEBHOOK_SECRET in Railway env

6. **Smoke Test**:
   - Open Vercel URL in browser
   - Login as demo auditor-viewer (read-only)
   - Navigate to `/razorpay` page
   - Click "Generate test payment"
   - Observe reconciliation run trigger and match-rate update
   - Download accuracy report from `/accuracy` page

7. **E2E Validation**:
   - Full path test (see testing.md §5 manual QA checklist)
   - Timed under 5 minutes
   - Run by someone who didn't build the code

---

## Files to Change Summary

### For Settlement Lag Calibration:
- [api/reconciliation/service.py](api/reconciliation/service.py)
- [api/forecast.py](api/forecast.py)
- [tests/test_v1_features.py](tests/test_v1_features.py)

### For Test-Payment Capture:
- [api/integrations/razorpay/client.py](api/integrations/razorpay/client.py)
- [api/razorpay.py](api/razorpay.py)
- [api/main.py](api/main.py)

### For Frontend:
- All files in [apps/web/app/](apps/web/app/) (pages needing verification/completion)
- Potentially [apps/web/components/](apps/web/components/) (UI fixes)

---

## Summary

**Original Feature Set**: 20 Functional Requirements (FR-1 through FR-20)  
**Implemented & Tested**: 17/20 ✅  
**Required Before Deployment**: 3/20 (settlement lag, test-payment capture, frontend QA)  
**Post-V1 / Optional**: Live Razorpay, multi-currency, multi-tenant (explicitly deferred)

**Recommendation**: Implement the three required items (est. 5 hours), run validation suite, then proceed to deployment.

---

**Audit Date**: 2026-09-05  
**Auditor**: Deployment Readiness Checker  
**Status**: Ready for implementation phase
