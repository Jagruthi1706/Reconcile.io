# AI Finance Controller

Autonomous reconciliation, tax-line matching, cash forecasting, and a settlement Q&A copilot — closing the finance-ops loop across bank feeds, GL, and **live Razorpay test-mode data**, with match rate, precision/recall/F1, and an honest exception list reported at every run.

> **Status:** build in progress · **Mode:** Razorpay **test mode** only, everywhere, always (see the `TEST MODE` badge in the app shell) · **Docs:** this file is the index — see the table below for everything else.

---

## Why this exists

Reconciliation, settlement matching, and cash forecasting are still mostly done by hand across finance teams, even as verification — not generation — has become the actual bottleneck for AI-assisted work. This project is an agent that closes that loop end to end: it ingests from multiple sources, matches them with an auditable tiered engine, classifies tax treatment, forecasts 13 weeks of cash, answers questions about all of it with citations, and — critically — **measures its own accuracy against a labeled golden set** instead of asserting it.

## Doc index

| Doc | What's in it |
|---|---|
| [`project.spec.md`](./project.spec.md) | Problem statement, goals/non-goals, personas, functional requirements, success metrics |
| [`architecture.md`](./architecture.md) | System diagram, data flow, database schema, sequence diagrams |
| [`agent.md`](./agent.md) | What's agentic vs. assistant, engine boundaries, Claude tool contract, guardrails |
| [`decisions.md`](./decisions.md) | ADR log — every material decision, with context and consequences |
| [`api_spec.md`](./api_spec.md) | REST endpoint reference |
| [`environment.md`](./environment.md) | Env vars, local setup, Docker Compose, key acquisition |
| [`testing.md`](./testing.md) | Test strategy, accuracy benchmark harness, CI gates |
| [`tasks.md`](./tasks.md) | Epic/task breakdown with checkboxes |
| [`roadmap.md`](./roadmap.md) | Phased build plan and milestones |

## Quickstart

```bash
git clone <repo-url> ai-finance-controller && cd ai-finance-controller
cp .env.example .env               # fill in RAZORPAY_* and (optional) ANTHROPIC_API_KEY — see environment.md
make dev                           # docker compose up: postgres, redis, backend, worker, frontend
make seed                          # loads demo ledger data + the golden accuracy dataset
make bench                         # runs the accuracy harness, prints precision/recall/F1
```

Open:
- `http://localhost:3000` — the app (starts on `/pitch`)
- `http://localhost:8000/docs` — live FastAPI/OpenAPI reference (source of truth behind `api_spec.md`)

No `ANTHROPIC_API_KEY`? The app runs fine — the Copilot page falls back to structured-only answers, nothing else degrades.

## Repo layout

```
ai-finance-controller/
├── apps/
│   ├── web/            # Next.js 14 frontend
│   └── api/             # FastAPI backend + engines
├── packages/
│   └── engine/           # reconciliation / tax / forecast / accuracy engines (pure Python, importable + testable standalone)
├── infra/
│   ├── docker-compose.yml
│   └── migrations/       # Alembic
├── data/
│   ├── seed/             # demo dataset
│   └── golden/           # labeled accuracy benchmark set
└── docs/                 # this doc set
```

## One-line pitch for a judge in a hurry

Feed it a bank statement, a GL export, and a Razorpay test account — it tells you, with receipts, what matches, what doesn't, why, what your tax exposure looks like, and what your cash position will be in 13 weeks, and it can prove its own accuracy on demand.
