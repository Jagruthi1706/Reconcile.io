# decisions.md — Architecture Decision Records

Format: **Context → Decision → Consequences.** Numbered, never renumbered — a superseded ADR is marked superseded, not deleted.

---

### ADR-001: Frontend framework — Next.js 14 (App Router) + TypeScript
**Context**: Need server-rendered data-heavy dashboards, fast judge-facing deploy, strong table/chart ecosystem.
**Decision**: Next.js 14 App Router, TypeScript throughout.
**Consequences**: React Server Components reduce client bundle for read-heavy pages; file-based routing maps directly to the page list in the UX blueprint; Vercel deploy is trivial. Trade-off: App Router's caching model needs explicit `revalidate`/`no-store` handling on polling endpoints (run status) — documented in `api_spec.md`.

### ADR-002: Backend framework — FastAPI (Python 3.11)
**Context**: The engines (reconciliation, tax, forecast) are naturally pandas/numpy Python; a separate API language would mean re-implementing or wrapping them.
**Decision**: FastAPI as the single backend, engines imported as a local package (`packages/engine`), not called over a network boundary.
**Consequences**: One language for API + engine keeps `api_spec.md` and the OpenAPI docs auto-generated and always in sync. Trade-off: Python async ecosystem is less mature than Node's for some integrations — mitigated by using `httpx` (async-native) for the Razorpay client.

### ADR-003: Database — PostgreSQL 15, no NoSQL layer
**Context**: Financial data needs ACID guarantees and relational integrity between ledger lines, matches, and exceptions.
**Decision**: Postgres only, JSONB columns for raw source payloads instead of a separate document store.
**Consequences**: One database to operate, back up, and migrate. Trade-off: JSONB querying is less ergonomic than a native document DB for deep payload inspection — acceptable since payloads are for audit reference, not primary querying.

### ADR-004: Claude never decides a match, classification, or forecast number
**Context**: An LLM-decided match is unauditable and non-reproducible — unacceptable for financial reconciliation.
**Decision**: All matching/classification/forecasting logic is deterministic Python. Claude is invoked only for the Copilot's natural-language explanation layer, with read-only tools and enforced citation verification (see `agent.md` §4).
**Consequences**: Every number in the product is reproducible without any LLM call. The Copilot can be disabled entirely with zero impact on core accuracy. Trade-off: explanations are only as good as the structured data retrieved — mitigated by the citation-verification pass.

### ADR-005: Razorpay Test Mode as the settlement source of truth
**Context**: Needed a real, testable payment-processor integration rather than a synthetic settlement simulator, to prove the product against a live API.
**Decision**: Integrate Razorpay's Orders, Payments, Refunds, Settlements APIs and the `/v1/settlements/recon/combined` report, plus webhooks, in test mode only.
**Consequences**: The recon-combined endpoint gives payment↔settlement↔fee↔tax↔UTR mapping directly from Razorpay — strong ground truth for the reconciliation engine to match against. Trade-off: recon-combined availability can depend on account configuration; the ingestion connector falls back to composing the same mapping from `/settlements` + `/payments` if recon-combined isn't available on a given test account (documented in `environment.md`).

### ADR-006: Accuracy is measured against a labeled golden set, in CI, every change
**Context**: "85% match rate" on one run proves nothing about generalization or regression risk.
**Decision**: Maintain `golden_labels` (hand-labeled known-correct/incorrect pairs); every engine-touching PR runs the benchmark in CI; results stored in `accuracy_benchmarks` and charted.
**Consequences**: Accuracy claims are falsifiable and trend-visible. Trade-off: golden set maintenance is ongoing work — assigned as an explicit task in `tasks.md`, not left implicit.

### ADR-007: Ledger visual identity as the product's design language
**Context**: A generic Tailwind/shadcn dashboard is forgettable in a field of similar entries.
**Decision**: Carry the ink/parchment, tabular-monospace, serif-heading aesthetic from the prototype into the full product, applied consistently across all 11 pages.
**Consequences**: Distinctive, on-brand for a finance product, low risk of reading as templated. Trade-off: some shadcn defaults need overriding rather than used as-is — scoped in the frontend design tokens file, not ad hoc per page.

### ADR-008: Background processing — Celery + Redis
**Context**: Reconciliation runs, webhook processing, and scheduled forecast recalculation must not block API request threads.
**Decision**: Celery workers, Redis as broker and cache.
**Consequences**: Clean separation between request/response and long-running work; live progress polling from the frontend. Trade-off: one more moving part in `docker-compose.yml` — accepted, it's one line.

### ADR-009: Auth roles include a read-only judge/evaluator login
**Context**: The product will be evaluated by people who should not be able to mutate demo data mid-review.
**Decision**: `auditor-viewer` role — full read access to every page, zero write endpoints reachable.
**Consequences**: Demo data integrity is protected without gating access behind a "please don't touch anything" warning.

### ADR-010: Export formats — PDF (WeasyPrint), XLSX (openpyxl), CSV
**Context**: Different audiences need different export shapes — a board wants a PDF, an auditor wants a raw ledger.
**Decision**: Server-side generation, three formats, one export endpoint family.
**Consequences**: No client-side PDF library weight in the frontend bundle. Trade-off: PDF layout changes require a backend deploy, not a frontend one — acceptable given exports are a controller-owned artifact, not end-user customizable in v1.
