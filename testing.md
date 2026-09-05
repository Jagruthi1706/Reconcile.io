# testing.md

## 1. Philosophy
Two different kinds of "correct" are tested separately and never conflated: **code correctness** (does the function do what it says) and **domain accuracy** (does the reconciliation engine actually get the right answer on real-shaped data). A green test suite with a degrading accuracy benchmark is a failing build.

## 2. Test layers

| Layer | Tool | Scope |
|---|---|---|
| Unit | `pytest` | Tier 1–4 matching logic, tax rule classifier, forecast math, citation-verification logic — each in isolation with synthetic fixtures |
| Integration | `pytest` + `httpx.AsyncClient` | API routes against a real (test-container) Postgres; Celery tasks run in eager mode |
| Contract | `pytest` + recorded fixtures | Razorpay webhook signature verification and payload parsing against saved real test-mode payloads (checked into `data/fixtures/razorpay/`), so tests don't depend on live API availability |
| Frontend unit | `vitest` + React Testing Library | Component-level: table rendering, chart data transforms, citation-chip rendering |
| E2E | `playwright` | Full page flows — see §4 |
| Accuracy | custom harness (`packages/engine/bench.py`), `scikit-learn` metrics | Golden-set precision/recall/F1/confusion matrix |

## 3. Accuracy benchmark harness (the important one)
- **Golden set**: `data/golden/labels.jsonl` — hand-labeled pairs `{line_a_id, line_b_id, expected_match: bool, notes}`, seeded from a mix of Razorpay test-mode payments and deliberately-noisy bank/GL fixtures (missing references, amount drift, timing gaps — the same noise categories the prototype engine already injects).
- **Run**: `make bench` → runs the current engine over the golden set → prints and persists precision, recall, F1, and the 4-cell confusion matrix.
- **CI gate**: any PR touching `packages/engine/**` runs the benchmark automatically; the build fails if F1 drops more than 2 points from the value stored for the current `main`, or if **false-match count increases at all** (a stricter gate than F1, because a wrong match is worse than a missed one in a finance product).
- **Growing the golden set is a tracked task**, not an afterthought — see `tasks.md` Epic 7. Target: 150+ labeled pairs by the demo milestone, covering every reason code at least 5 times.

## 4. E2E coverage (Playwright) — one spec per page, minimum
| Page | Critical path tested |
|---|---|
| Pitch/Landing | Hero stat renders a real number (not a placeholder), CTA reaches the live console |
| Overview | KPI band matches the latest run's numbers; "Run Reconciliation Now" completes and updates the page |
| Reconciliation Workbench | Filter → drill into a match → side-by-side diff renders correctly; override writes to audit log |
| Exception Explorer | Kanban drag between statuses persists; aging heatmap reflects `opened_at` |
| Tax-Line Matcher | Confirming a review-queue item removes it from the queue and appears in `audit_log` |
| Cash Forecast | Scenario slider changes the chart without a full page reload |
| Copilot | A question about a known exception returns an answer whose citation deep-links correctly; structured-mode toggle changes the response format |
| Razorpay Live Console | End-to-end: generate test payment → pull settlement → run reconciliation → match-rate delta visibly updates |
| Accuracy | "Run Benchmark" produces a new point on the trend chart |
| Audit & Export | Each export format downloads and opens without corruption |
| Settings | Changing a matching tolerance and re-running a reconciliation changes the result accordingly |

## 5. Manual QA checklist (pre-demo)
- [ ] Fresh `git clone` → `make dev` → `make seed` → `make bench` succeeds with no manual intervention
- [ ] App boots with `ANTHROPIC_API_KEY` unset and every page still functions
- [ ] `RAZORPAY_MODE=live` in `.env` causes the app to refuse to boot (hard guard verified, not just documented)
- [ ] Judge/`auditor-viewer` login cannot reach any write endpoint (verified via direct API call, not just hidden UI)
- [ ] All 11 pages navigable via `⌘K` palette without using the sidebar
- [ ] Every chart/table has a non-empty state on a fresh seed (no "undefined" or blank panels)

## 6. Test data management
- `data/seed/` — realistic demo dataset for the UI walkthrough (not used for accuracy scoring).
- `data/golden/` — labeled accuracy set (used only by the benchmark harness, never mixed into demo seed data).
- `data/fixtures/razorpay/` — recorded real API responses for contract tests, refreshed manually against a live test account periodically (not on every CI run, to avoid rate limits/flakiness).
- A nightly (non-blocking) CI job hits the real Razorpay test API once to catch upstream contract drift early, separate from the PR-blocking suite which uses fixtures.
