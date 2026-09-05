# project.spec.md

## 1. Problem statement
Finance teams close the books by hand: matching bank lines to GL entries, chasing settlement batches from payment processors, classifying transactions for tax, and rebuilding a cash forecast in a spreadsheet — every cycle, from scratch, with the audit trail living in someone's memory. The bottleneck in 2026 isn't generating numbers, it's *verifying* them fast enough and *trusting* the result enough to act on it.

## 2. Goals
1. Close one real finance-ops loop — multi-source reconciliation — end to end, against **live Razorpay test-mode data**, not a static CSV.
2. Report accuracy as a real metric (precision/recall/F1 against a labeled golden set), not a single cherry-picked run.
3. Extend the same audit trail into tax classification, cash forecasting, and a natural-language copilot, so all four are provably built on the same facts.
4. Ship a UI a non-technical evaluator can navigate unassisted and come away understanding exactly what happened and why.
5. Keep every AI (Claude) contribution clearly separated from the deterministic engine's decisions — explainer, never decision-maker.

## 3. Non-goals (v1)
- Not a full double-entry accounting system or ERP replacement — it reconciles and explains, it doesn't post journal entries back to an ERP.
- Not multi-tenant SaaS — single organization/workspace per deployment for v1.
- Not live-mode payments — Razorpay integration is test-mode only, enforced in code, not just convention.
- Not a general-purpose BI tool — every chart answers a specific finance-ops question, nothing exploratory/ad-hoc.
- Not real bank API connectivity — bank side is CSV upload for v1 (no Plaid/account-aggregator integration yet; see `roadmap.md`).

## 4. Personas
| Persona | Role | What they need from this product |
|---|---|---|
| **Priya, Controller** | Owns the close | Trustworthy match rate, a short honest exception list, one-click export for the board |
| **Dev, Staff Accountant** | Does the manual matching today | A workbench that shows *why* something didn't match, not just that it didn't |
| **Amara, Tax Analyst** | Reviews tax treatment | A queue of only the ambiguous lines, not all of them |
| **CFO** | Reads the forecast | 13-week cash position with a visible low point and the assumptions behind it |
| **Judge / evaluator** | Assesses the product cold | A landing page, a live-data proof point, and an accuracy page that isn't just a marketing claim |

## 5. Functional requirements
### 5.1 Ingestion
- FR-1: Pull Razorpay test-mode Orders, Payments, Refunds, Settlements, and the Settlement Recon Combined report via API.
- FR-2: Accept a bank-statement CSV and a GL-export CSV with a user-configurable column mapping.
- FR-3: Receive and verify Razorpay webhooks (`payment.captured`, `settlement.processed`, `refund.processed`) and normalize into the canonical ledger schema in near-real-time.
- FR-4: Every raw source payload is retained (JSONB) alongside the normalized record — nothing is lossy-transformed.

### 5.2 Reconciliation
- FR-5: Tiered matching — exact reference (Tier 1), tolerance-based amount/date (Tier 2), description-similarity for reference-stripped lines (Tier 3), embedding-similarity fallback (Tier 4).
- FR-6: Every match carries a tier, a numeric confidence, and a variance; every non-match carries a machine-readable reason code.
- FR-7: Match rate reported both by line count and by dollar value.
- FR-8: Every reconciliation run is versioned and retained; nothing overwrites history.

### 5.3 Tax
- FR-9: Every GL/opex line classified to a jurisdiction/treatment label with a confidence score.
- FR-10: Lines below the confidence threshold route to a human review queue; a human correction becomes a labeled training example.

### 5.4 Forecast
- FR-11: 13-week cash projection from an aging/collection-probability model.
- FR-12: The model recalibrates its collection curve using the settlement lag observed in the latest reconciliation run.
- FR-13: User-adjustable best/base/worst scenario inputs (opex, AR velocity) recompute the forecast live.

### 5.5 Copilot
- FR-14: Natural-language Q&A grounded in the structured ledger/match/exception tables; SQL retrieval first, Claude formats second.
- FR-15: Every answer that references a record must cite its ID, and the ID must be verified to exist in the retrieved context before the answer is returned — no citation, no claim.

### 5.6 Accuracy
- FR-16: A hand-labeled golden dataset with known-correct matches.
- FR-17: Precision, recall, F1, and a 4-cell confusion matrix (correct match / missed match / false match / correct exception) computed on demand and in CI.
- FR-18: Metric history retained and charted over engine versions.

### 5.7 Audit & export
- FR-19: Immutable, append-only audit log of every state change (match override, tax correction, exception resolution).
- FR-20: Export to PDF (board report), XLSX (raw ledger), CSV (exceptions).

## 6. Success metrics
| Metric | v1 target | How it's measured |
|---|---|---|
| Match rate (count) | ≥ 85%, trending up | `reconciliation_runs.match_rate_count` |
| Match rate ($) | ≥ 85%, trending up | `reconciliation_runs.match_rate_dollar` |
| F1 on golden set | ≥ 0.85, tracked per engine version | `accuracy_benchmarks` |
| False-match rate | as close to 0 as possible — tracked separately, never averaged away | confusion matrix `FP` cell |
| Time to explain an exception | < 5 seconds via Copilot | manual QA |
| Judge can navigate unassisted | yes/no per test | usability pass, see `testing.md` §5 |

## 7. Out-of-scope questions this doc deliberately doesn't answer
Pricing/billing model, multi-currency consolidation beyond simple FX display, live-mode payment support — all deferred to `roadmap.md` "later" phases if pursued past v1.
