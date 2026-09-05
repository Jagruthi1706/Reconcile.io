# agent.md

## 1. What "agent" means in this codebase
Two different things share the word, and this doc keeps them separate on purpose:

1. **The autonomous loop** (ingest → match → classify → project) — runs on a schedule or trigger, makes deterministic decisions, no LLM in the decision path. This is the "agent" that closes the books.
2. **The Copilot** — a Claude-backed conversational layer that *explains* what the loop already decided. It never matches, classifies, or forecasts on its own authority.

If a judge asks "is this an AI agent or a chatbot with a dashboard," the honest answer is: it's an autonomous deterministic agent with a chatbot bolted on for explanation — and that split is the point, not a limitation.

## 2. The five engines

| Engine | Autonomous loop or Copilot-only? | Decides | Never decides |
|---|---|---|---|
| Reconciliation | Autonomous loop | Which lines match, at what tier/confidence | — |
| Tax | Autonomous loop | Jurisdiction/treatment label, confidence | Final classification below threshold — routes to human |
| Forecast | Autonomous loop | 13-week projection from the calibrated model | Actual future cash — it's a projection, labeled as such everywhere in the UI |
| Copilot | Claude-backed | How to phrase an explanation, which retrieved rows are relevant to surface | Whether something is a match, a tax label, or a forecast number |
| Accuracy | Autonomous loop | Precision/recall/F1 against golden labels | — (no subjectivity: it's arithmetic over known-correct labels) |

## 3. Reconciliation engine — tier logic (the part everything else depends on)
- **Tier 1 — exact reference**: same reference ID present in both sources, amount matches to the cent → confidence 1.00.
- **Tier 2 — reference match, tolerant amount/date**: same reference ID, amount within 1.5% (fee/FX rounding), date within a 5-day window → confidence scaled by how close the amount is.
- **Tier 3 — description similarity**: no usable reference on one side; amount exact, date within window, token-overlap similarity on description → confidence from the similarity score.
- **Tier 4 — embedding fallback** *(v1.1 addition over the prototype)*: nothing above resolved it; cosine similarity between description embeddings, combined with amount/date proximity, above a strict threshold → confidence capped below auto-accept, always routed to "needs review," never auto-matched. This tier exists to catch real matches the earlier tiers miss, without ever silently trusting a fuzzy semantic guess.
- **No match**: classified with a `reason_code` (see `api_spec.md` for the enumerated list) — never left as a bare "unmatched."

**Auto-accept threshold**: confidence ≥ 0.90 posts without human review. Below that, the line surfaces in the Reconciliation Workbench as "needs review" — a human, not the engine, closes it out.

## 4. Claude tool contract (Copilot)
Claude is called with a **fixed, read-only tool set** — no tool can write to the database:

```
get_record(id: str) -> ledger_lines | matches | exceptions row
get_exceptions(filters: {status, reason_code, source, date_range}) -> list
get_match_rate(run_id: str | "latest") -> { count_pct, dollar_pct }
get_forecast(run_id: str | "latest") -> forecast_snapshot
get_tax_summary(jurisdiction: str | "all") -> aggregated tax_classifications
```

**System prompt constraints (enforced, not just requested):**
- Every factual claim referencing a record must include that record's ID in `[brackets]`.
- Before the answer is returned to the user, the API layer re-checks that every bracketed ID in Claude's draft actually appears in the tool results passed as context. Any ID that doesn't verify is stripped and the answer is regenerated once with an explicit instruction to only cite provided IDs; if it fails twice, the API returns the structured (non-Claude) answer instead and logs the failure.
- Claude is never given write access, never given the ability to change a match, exception status, or tax label — those actions exist only as explicit user-initiated API calls from the Workbench/Exception Explorer/Tax pages, each captured in `audit_log`.
- No `ANTHROPIC_API_KEY` set → Copilot falls back to a templated structured-answer mode (same underlying `get_*` tools, no natural-language generation) — the product's core loop never depends on Claude being available.

## 5. Guardrails summary
| Risk | Guardrail |
|---|---|
| Claude hallucinates a match that doesn't exist | Citation-verification pass before any answer reaches the user |
| Claude asked to "just fix" a mismatch | No write tools exist; the request is answered with an explanation and a link to the manual-override UI, which logs the human decision |
| Tier-4 embedding match silently trusted | Hard-capped confidence, never auto-accepted, always human-reviewed |
| Tax engine over-confident on an ambiguous line | Confidence threshold gates auto-classification; correction becomes a labeled example, not a silent overwrite |
| Forecast presented as fact | UI always labels it "projected," always shows the calibration inputs (settlement lag, scenario assumptions) alongside the number |
| Accuracy number becomes a vibe again | Computed only from `golden_labels` vs. engine output — no manual metric entry path exists in the schema |
