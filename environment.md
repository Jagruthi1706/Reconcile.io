# environment.md

## 1. Required tooling
| Tool | Version | Notes |
|---|---|---|
| Node.js | 20+ | via `nvm` recommended |
| pnpm | 9+ | `corepack enable` gives you this for free |
| Python | 3.11+ | `uv` recommended over Poetry for speed |
| Docker + Compose | v2 | only local dependency requirement |
| `make` or `just` | latest | task runner |

## 2. Environment variables (`.env.example`)
```ini
# --- App ---
APP_ENV=development
API_PORT=8000
WEB_PORT=3000
JWT_SECRET=change-me-in-dev-too

# --- Database ---
DATABASE_URL=postgresql+asyncpg://afc:afc@localhost:5432/afc
REDIS_URL=redis://localhost:6379/0
CORS_ORIGINS=http://localhost:3000

# --- Razorpay (TEST MODE ONLY — never put live keys in this project) ---
RAZORPAY_KEY_ID=rzp_test_xxxxxxxxxxxx
RAZORPAY_KEY_SECRET=xxxxxxxxxxxxxxxxxxxx
RAZORPAY_WEBHOOK_SECRET=whsec_xxxxxxxxxxxx
RAZORPAY_MODE=test          # hard guard: app refuses to boot if this isn't "test"

# --- Anthropic (optional) ---
ANTHROPIC_API_KEY=           # leave blank to run Copilot in structured-only mode
ANTHROPIC_MODEL=claude-sonnet-4-6
GEMINI_API_KEY=              # optional Copilot provider
GEMINI_MODEL=gemini-2.0-flash

# --- Vercel frontend ---
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000/api/v1

# --- Matching engine tunables (defaults; editable later from Settings UI) ---
MATCH_AUTO_ACCEPT_CONFIDENCE=0.90
MATCH_AMOUNT_TOLERANCE_PCT=1.5
MATCH_DATE_WINDOW_DAYS=5
```

## 3. Acquiring a Razorpay test account
1. Sign up at the Razorpay dashboard, no business verification needed for **test mode**.
2. Dashboard → **Settings → API Keys → Generate Test Key** → copy `Key Id` / `Key Secret` into `.env`.
3. Dashboard → **Settings → Webhooks → Add New Webhook**, point it at `https://<your-tunnel>/api/v1/webhooks/razorpay` (use `ngrok`/`cloudflared` for local dev), subscribe to `payment.captured`, `settlement.processed`, `refund.processed`, copy the generated secret into `RAZORPAY_WEBHOOK_SECRET`.
4. Use Razorpay's published test card numbers (dashboard → Test Cards) to generate real test payments from the Razorpay Live Test Console page.
5. If `/v1/settlements/recon/combined` returns empty/unavailable on your test account, the connector automatically falls back to composing the same view from `/v1/settlements` + `/v1/payments` — no config needed, logged as a connector-mode notice in `/razorpay/activity`.

## 4. Acquiring an Anthropic API key (optional)
1. `console.anthropic.com` → Create API key.
2. Paste into `ANTHROPIC_API_KEY`. Leave blank to skip — the app boots and runs identically, Copilot just won't do natural-language phrasing.

## 5. `docker-compose.yml` — services
| Service | Image/build | Port | Depends on |
|---|---|---|---|
| `web` | `apps/web` (Next.js) | 3000 | `api` |
| `api` | `apps/api` (FastAPI) | 8000 | `postgres`, `redis` |
| `worker` | same image as `api`, `CMD celery worker` | — | `postgres`, `redis` |
| `postgres` | `postgres:15` | 5432 | — |
| `redis` | `redis:7` | 6379 | — |

## 6. Bootstrap
```bash
cp .env.example .env         # fill in Razorpay keys at minimum
make dev                     # docker compose up --build
make migrate                 # alembic upgrade head (also runs automatically on api boot in dev)
make seed                    # demo ledger data + golden accuracy set
make bench                   # sanity-check the accuracy harness runs
```

## 7. Common issues
| Symptom | Fix |
|---|---|
| App refuses to boot, error mentions `RAZORPAY_MODE` | You put a live key in `.env` — this is a hard guard, use `rzp_test_...` only |
| Webhooks never arrive locally | Razorpay can't reach `localhost` — use `ngrok http 8000` and update the dashboard webhook URL |
| Copilot returns structured answers only, no prose | Expected with no `ANTHROPIC_API_KEY` — not a bug |
| `make bench` shows F1 dropping after a change | CI will also catch this — check `packages/engine/tests/` for the specific regressed case before merging |
