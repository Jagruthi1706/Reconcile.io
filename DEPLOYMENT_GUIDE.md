# DEPLOYMENT GUIDE — Reconcile.io v1.0
## GitHub → Railway → Vercel

**Status**: Code Freeze ✅ — Ready for Production Deployment  
**Last Updated**: 2026-09-05  
**Backend Framework**: FastAPI (Python 3.11)  
**Frontend Framework**: Next.js 14 (Node 20)  
**Database**: PostgreSQL 15 (async)  
**Message Broker**: Redis 7  
**Background Jobs**: Celery

---

## DEPLOYMENT SEQUENCE (Step-by-Step)

### Step 1: Prepare Repository

```bash
# Ensure all changes are committed
cd /path/to/reconcile_io
git status  # Should be clean

# Verify migrations are current
python -m alembic heads  # Should show: 0004_settlement_lag (head)

# Verify all tests pass
python -m pytest tests/ api/integrations/razorpay/tests/ packages/engine/tests/ -q
# Expected: 57 passed, 2 skipped

# Verify frontend builds
cd apps/web
pnpm build
# Expected: ✓ Compiled successfully

# Push to GitHub
git push origin main
```

### Step 2: Create Railway Project (API & Worker)

```bash
# Install Railway CLI
npm install -g @railway/cli

# Login and create project
railway login
railway init
# When prompted: "Create a new project"
# Name: reconcile-io-api
```

### Step 3: Add PostgreSQL Service to Railway

```bash
railway add
# Select: PostgreSQL
# This creates DATABASE_URL automatically
railway status  # Note the PostgreSQL connection string
```

### Step 4: Add Redis Service to Railway

```bash
railway add
# Select: Redis
# This creates REDIS_URL automatically
railway status  # Note the Redis connection string
```

### Step 5: Configure Environment Variables on Railway

```bash
# Set all required environment variables (see section below)
# DO NOT print or expose secret values

railway env:set RAZORPAY_KEY_ID=<value-from-dashboard>
railway env:set RAZORPAY_KEY_SECRET=<secure-value>
railway env:set RAZORPAY_WEBHOOK_SECRET=<secure-value>
railway env:set JWT_SECRET=<generate-secure-random-value>
railway env:set ANTHROPIC_API_KEY=<optional>
railway env:set GEMINI_API_KEY=<optional>
railway env:set APP_ENV=production
railway env:set CORS_ORIGINS=https://web-domain.vercel.app
railway env:set NEXT_PUBLIC_API_BASE_URL=https://api-service.railway.app/api/v1

# Verify env variables are set (without exposing values)
railway env:list
```

### Step 6: Run Database Migrations

```bash
# Apply all pending migrations to the Railway PostgreSQL
railway run python -m alembic upgrade head

# Seed demo data (optional, for staging only)
railway run python data/seed/seed.py

# Verify migration status
railway run python -m alembic current
# Expected: 0004_settlement_lag
```

### Step 7: Deploy API Service

```bash
# Connect Railway to GitHub
railway connect
# Provide GitHub token
# Select your repository

# Deploy the API service
railway deploy
# Will use Dockerfile at: infra/Dockerfile.api
# Expected: ✓ Deployment successful

# Get the API service URL
railway status
# Note: https://api-xxxx.railway.app
```

### Step 8: Deploy Celery Worker Service

```bash
# Add another service for the worker
railway service add worker
# Build config: Docker (Dockerfile.api)
# Custom CMD: celery -A api.worker celery_app worker --loglevel=info

# Set environment variables for worker
railway env:set WORKER_CMD="celery -A api.worker celery_app worker --loglevel=info"

# Deploy worker
railway up
```

### Step 9: Setup Frontend on Vercel

```bash
# Install Vercel CLI
npm i -g vercel

# Login to Vercel
vercel login

# Deploy frontend (in apps/web directory)
cd apps/web
vercel --prod
# Link to existing project if one exists
# Set build output: .next
# Install command: pnpm install --frozen-lockfile
# Build command: pnpm build
# Start command: pnpm start

# Get the frontend URL
vercel env:list  # Note the URL
```

### Step 10: Configure Environment Variables on Vercel

```bash
# Set frontend environment variable
vercel env:set NEXT_PUBLIC_API_BASE_URL https://api-xxxx.railway.app/api/v1 --prod
# (Replace api-xxxx with your actual Railway API service name)
```

### Step 11: Configure Razorpay Webhook

```bash
# Login to Razorpay Dashboard
# Dashboard → Settings → Webhooks → Add New Webhook

# Webhook URL: https://api-xxxx.railway.app/api/v1/webhooks/razorpay
# Events to subscribe:
#   ✓ payment.captured
#   ✓ settlement.processed
#   ✓ refund.processed
# Secret: (matches RAZORPAY_WEBHOOK_SECRET in Railway env)

# Save webhook configuration
# Test webhook delivery
```

### Step 12: Smoke Tests (5-Minute Validation)

```bash
# See "SMOKE TEST CHECKLIST" section below
```

---

## REQUIRED ENVIRONMENT VARIABLES

### Production Environment (Railway)

| Variable | Value | Source | Required? |
|----------|-------|--------|-----------|
| `APP_ENV` | `production` | Manual | Yes |
| `API_PORT` | `8000` | Automatic (Railway) | Yes |
| `DATABASE_URL` | `postgresql+asyncpg://...` | Railway PostgreSQL | Yes |
| `REDIS_URL` | `redis://...` | Railway Redis | Yes |
| `JWT_SECRET` | `<generate-random-secure-string>` | Manual | Yes |
| `RAZORPAY_MODE` | `test` | Manual (hardcoded to "test") | Yes |
| `RAZORPAY_KEY_ID` | `rzp_test_xxxxxxxxxxxxx` | Razorpay Dashboard | Yes |
| `RAZORPAY_KEY_SECRET` | `<secure-value>` | Razorpay Dashboard | Yes |
| `RAZORPAY_WEBHOOK_SECRET` | `<secure-value>` | Razorpay Dashboard | Yes |
| `CORS_ORIGINS` | `https://web-domain.vercel.app` | Manual | Yes |
| `NEXT_PUBLIC_API_BASE_URL` | `https://api-xxxx.railway.app/api/v1` | Manual | Yes |
| `ANTHROPIC_API_KEY` | `sk-ant-...` | Anthropic (optional) | No |
| `ANTHROPIC_MODEL` | `claude-sonnet-4-6` | Manual (optional) | No |
| `GEMINI_API_KEY` | `AIza...` | Google (optional) | No |
| `GEMINI_MODEL` | `gemini-2.0-flash` | Manual (optional) | No |
| `MATCH_AUTO_ACCEPT_CONFIDENCE` | `0.90` | Manual (tunable) | No |
| `MATCH_AMOUNT_TOLERANCE_PCT` | `1.5` | Manual (tunable) | No |
| `MATCH_DATE_WINDOW_DAYS` | `5` | Manual (tunable) | No |

### Environment Variable Generation

**JWT_SECRET** (must be secure random string):
```bash
# Generate 32-byte secure random value (base64)
python -c "import secrets; print(secrets.token_urlsafe(32))"
# Output: <copy this value into RAILWAY JWT_SECRET>
```

**Do NOT expose these in logs, console output, or version control**

---

## BUILD & START COMMANDS

### Backend (API Service) — Railway

**Build**:
```bash
# Automatic — Railway uses Dockerfile.api
# infra/Dockerfile.api (lines 1-11):
# - Installs Python 3.11
# - Installs project dependencies from pyproject.toml
# - Sets PYTHONPATH=/app
```

**Start**:
```bash
# Automatic — Default CMD in Dockerfile.api
uvicorn api.main:app --host 0.0.0.0 --port 8000

# Or manually (if needed):
railway run uvicorn api.main:app --host 0.0.0.0 --port 8000
```

**Health Check**:
```bash
curl https://api-xxxx.railway.app/health
# Expected response: {"status": "ok"}
```

### Worker Service — Railway

**Build**:
```bash
# Same Dockerfile.api
```

**Start**:
```bash
celery -A api.worker celery_app worker --loglevel=info

# Verify worker is running:
railway logs  # Should show "Celery worker connected"
```

### Frontend (Web Service) — Vercel

**Build**:
```bash
# Automatic — Vercel uses next.config.js
cd apps/web
pnpm install --frozen-lockfile
pnpm build

# Output:
# ✓ Compiled successfully
# ✓ Linting and checking validity of types
# ✓ Collecting page data
# ✓ Generating static pages (15/15)
```

**Start**:
```bash
pnpm start

# Or automatically on Vercel:
# Vercel detects next.config.js and runs next start
```

---

## DATABASE MIGRATION COMMAND

**Apply all pending migrations**:
```bash
# Via Railway:
railway run python -m alembic upgrade head

# Or locally (for testing):
python -m alembic upgrade head

# Verify current migration:
railway run python -m alembic current
# Expected: 0004_settlement_lag

# Verify all heads:
railway run python -m alembic heads
# Expected: 0004_settlement_lag (head)

# Rollback (if needed):
railway run python -m alembic downgrade -1  # Rolls back one migration
```

**Migration Chain**:
```
┌─────────────────────────────────┐
│ 0001_initial_schema             │  ← Core tables (ledger_lines, reconciliation_runs, etc.)
│ ├─ Users, ApplicationSettings   │
│ ├─ Matches, Exceptions          │
│ └─ TaxClassifications, Forecasts│
└─────────────────┬───────────────┘
                  │
┌─────────────────▼───────────────┐
│ 0002_auth_settings              │  ← Auth & settings infrastructure
└─────────────────┬───────────────┘
                  │
┌─────────────────▼───────────────┐
│ 0003_razorpay_activity          │  ← Razorpay API logging
└─────────────────┬───────────────┘
                  │
┌─────────────────▼───────────────┐
│ 0004_settlement_lag (HEAD)       │  ← Settlement lag calibration
└─────────────────────────────────┘
```

---

## CELERY WORKER COMMAND

**Start Celery Worker**:
```bash
celery -A api.worker celery_app worker --loglevel=info

# For Railway service:
railway up --cmd "celery -A api.worker celery_app worker --loglevel=info"

# Configuration (from api/worker.py):
# - Broker: REDIS_URL
# - Backend: REDIS_URL (same)
# - Queue: default
# - Tasks imported from: api.tasks
#   ├─ reconcile.run(left_ids, right_ids)
#   └─ reconcile.all()
```

**Verify Worker Health**:
```bash
# Check worker is connected to Redis
railway logs  # Look for "Celery worker connected"

# Monitor active tasks
celery -A api.worker inspect active

# Check task statistics
celery -A api.worker inspect stats
```

**Registered Tasks** (api.tasks):
- `reconcile.run` — Run reconciliation on specific record sets
- `reconcile.all` — Run reconciliation on all records (called from webhook)

---

## RAZORPAY WEBHOOK CONFIGURATION

### Setup Steps

1. **Login to Razorpay Dashboard**
   - URL: https://dashboard.razorpay.com
   - Credentials: Your Razorpay test account

2. **Navigate to Webhooks**
   ```
   Settings → Webhooks → Add New Webhook
   ```

3. **Configure Webhook**
   ```
   Webhook URL: https://api-xxxx.railway.app/api/v1/webhooks/razorpay
   
   Events to Subscribe:
   ✓ payment.captured      (when a payment is captured)
   ✓ settlement.processed  (when settlement is processed)
   ✓ refund.processed      (when a refund is processed)
   
   Secret: <RAZORPAY_WEBHOOK_SECRET from Railway env>
   ```

4. **Save & Test**
   - Razorpay will generate the webhook secret
   - Copy this value into Railway env: `RAZORPAY_WEBHOOK_SECRET=<value>`
   - Click "Test Webhook" to verify delivery

### Webhook Processing Flow

```
Razorpay API
    ↓
POST /api/v1/webhooks/razorpay (HMAC-verified)
    ↓
api/webhooks.py::process_razorpay_webhook()
    ↓
Normalize payload → Ingest into ledger_lines
    ↓
Trigger: reconcile_all_task.delay()
    ↓
Celery Worker
    ↓
Execute reconciliation run
    ↓
Update: matches, exceptions, match_rate
```

### Testing Webhook (Live)

```bash
# Generate test payment via Razorpay Live Console page
# POST /razorpay/test-payment

# Or via curl:
curl -X POST https://api-xxxx.railway.app/api/v1/razorpay/test-payment \
  -H "Authorization: Bearer <jwt-token>" \
  -H "Content-Type: application/json" \
  -d '{"amount": 10000, "currency": "INR", "receipt": "order-001"}'

# Expected response:
# {"id": "order_...", "amount": 10000, ...}

# Watch logs for webhook delivery:
railway logs  # Look for "payment.captured"
```

---

## SMOKE TEST CHECKLIST (5 Minutes)

### Pre-Flight Checks

- [ ] All Railway services deployed and healthy
  ```bash
  railway status  # All services should be "running"
  ```

- [ ] PostgreSQL migrations applied
  ```bash
  railway run python -m alembic current
  # Expected: 0004_settlement_lag
  ```

- [ ] Redis broker connected
  ```bash
  railway logs  # Look for Celery "connected" message
  ```

- [ ] Frontend deployed on Vercel
  ```bash
  Open: https://web-xxxx.vercel.app
  ```

### 1. Health & Status

- [ ] API health endpoint
  ```bash
  curl https://api-xxxx.railway.app/health
  # Expected: {"status": "ok"}
  ```

- [ ] API Swagger docs available
  ```bash
  Open: https://api-xxxx.railway.app/docs
  # Expected: FastAPI Swagger UI loads
  ```

- [ ] Frontend loads without errors
  ```bash
  Open: https://web-xxxx.vercel.app/pitch
  # Expected: Landing page renders, hero stat visible
  ```

### 2. Authentication

- [ ] Create initial user via bootstrap
  ```bash
  curl -X POST https://api-xxxx.railway.app/api/v1/auth/bootstrap \
    -H "Content-Type: application/json" \
    -d '{"email": "admin@example.com", "password": "secure-password", "role": "controller"}'
  # Expected: {"user": {"email": "admin@example.com", "role": "controller"}}
  ```

- [ ] Login succeeds
  ```bash
  curl -X POST https://api-xxxx.railway.app/api/v1/auth/login \
    -H "Content-Type: application/json" \
    -d '{"email": "admin@example.com", "password": "secure-password"}'
  # Expected: {"access_token": "eyJ...", "user": {...}}
  ```

- [ ] Frontend login page works
  ```bash
  Open: https://web-xxxx.vercel.app/login
  Enter credentials above
  # Expected: Redirects to Overview page
  ```

### 3. Core Functionality

- [ ] Ledger lines endpoint accessible
  ```bash
  curl -X GET https://api-xxxx.railway.app/api/v1/ledger/lines \
    -H "Authorization: Bearer <jwt-token>"
  # Expected: [] (empty array initially)
  ```

- [ ] Create reconciliation run
  ```bash
  # Seed some demo data first:
  railway run python data/seed/seed.py
  
  # Then test API:
  curl -X GET https://api-xxxx.railway.app/api/v1/ledger/lines \
    -H "Authorization: Bearer <jwt-token>"
  # Expected: List of ledger lines (demo data)
  ```

- [ ] Trigger reconciliation
  ```bash
  curl -X POST https://api-xxxx.railway.app/api/v1/runs \
    -H "Authorization: Bearer <jwt-token>" \
    -H "Content-Type: application/json" \
    -d '{"left_record_ids": [...], "right_record_ids": [...]}'
  # Expected: {"run_id": "uuid"} with 202 status
  ```

- [ ] Poll reconciliation status
  ```bash
  curl -X GET https://api-xxxx.railway.app/api/v1/runs/{run_id} \
    -H "Authorization: Bearer <jwt-token>"
  # Expected: {"status": "done", "match_rate_count": X, ...}
  ```

### 4. Razorpay Integration

- [ ] Razorpay credentials configured
  ```bash
  # Check Railway env vars are set
  railway env:list | grep RAZORPAY
  # Expected: KEY_ID, KEY_SECRET, WEBHOOK_SECRET, MODE=test all present
  ```

- [ ] Create test payment via endpoint
  ```bash
  curl -X POST https://api-xxxx.railway.app/api/v1/razorpay/test-payment \
    -H "Authorization: Bearer <jwt-token>" \
    -H "Content-Type: application/json" \
    -d '{"amount": 10000, "currency": "INR", "receipt": "test-001"}'
  # Expected: Order created, payment captured, settlement pulled
  ```

- [ ] Webhook secret configured correctly
  ```bash
  # Monitor logs for webhook delivery
  railway logs | grep "payment.captured"
  # Expected: Webhook received and processed
  ```

### 5. Role-Based Access Control

- [ ] Controller can mutate
  ```bash
  # Login as controller, try to create a run
  # Should succeed
  ```

- [ ] Auditor-viewer (read-only) cannot mutate
  ```bash
  # Create auditor-viewer user:
  curl -X POST https://api-xxxx.railway.app/api/v1/auth/bootstrap \
    -H "Content-Type: application/json" \
    -d '{"email": "viewer@example.com", "password": "pwd", "role": "auditor-viewer"}'
  
  # Try to access protected endpoint:
  curl -X POST https://api-xxxx.railway.app/api/v1/runs \
    -H "Authorization: Bearer <auditor-token>"
  # Expected: 403 Forbidden
  ```

### 6. Frontend Pages (Navigate All 11)

- [ ] Page 0: `/pitch` (landing) — Hero stat loads
  ```bash
  Open: https://web-xxxx.vercel.app/pitch
  # Expected: Hero stat shows live match rate from DB
  ```

- [ ] Page 1: `/` (overview) — KPI band updates
  ```bash
  # Expected: Match rate, exceptions, cash forecast visible
  ```

- [ ] Page 2: `/reconcile` — Workbench loads
  ```bash
  # Expected: Table of ledger lines, side drawer for details
  ```

- [ ] Page 3: `/exceptions` — Kanban view
  ```bash
  # Expected: New → Investigating → Resolved → Written-off columns
  ```

- [ ] Page 4: `/tax` — Classification queue
  ```bash
  # Expected: Jurisdiction breakdown, review queue
  ```

- [ ] Page 5: `/forecast` — 13-week chart
  ```bash
  # Expected: Line chart, scenario sliders, low-point alert
  ```

- [ ] Page 6: `/copilot` — Chat interface
  ```bash
  # Expected: Chat UI, citation chips
  ```

- [ ] Page 7: `/razorpay` — Live console
  ```bash
  # Expected: "Generate test payment" button, real-time match update
  ```

- [ ] Page 8: `/accuracy` — Metrics page
  ```bash
  # Expected: F1 trend line, confusion matrix, "Run Benchmark" button
  ```

- [ ] Page 9: `/audit` — Audit log & export
  ```bash
  # Expected: Event log, export buttons (PDF/XLSX/CSV)
  ```

- [ ] Page 10: `/settings` — Admin panel
  ```bash
  # Expected: Razorpay key management, tax rules, matching tolerances
  ```

### 7. Export Functionality

- [ ] PDF export
  ```bash
  curl -X POST https://api-xxxx.railway.app/api/v1/export/pdf \
    -H "Authorization: Bearer <jwt-token>" \
    -H "Content-Type: application/json" \
    -d '{"report_type": "board"}'
  # Expected: PDF binary content, Content-Type: application/pdf
  ```

- [ ] XLSX export
  ```bash
  # Expected: Excel binary content
  ```

- [ ] CSV export
  ```bash
  # Expected: CSV text content
  ```

### 8. Background Jobs

- [ ] Celery worker processes tasks
  ```bash
  # Trigger a reconciliation via API
  # Check worker logs:
  railway logs  # Look for task processing logs
  # Expected: Task completes, results visible in API response
  ```

- [ ] Settlement lag calculated
  ```bash
  # Get latest forecast:
  curl -X GET https://api-xxxx.railway.app/api/v1/forecast/latest \
    -H "Authorization: Bearer <jwt-token>"
  # Expected: avg_settlement_lag is a number (not 0.00)
  ```

### 9. Final Judge Walkthrough (Timed: 5 Minutes)

**Scenario**: A non-technical evaluator landing on the product cold

```
1. Open https://web-xxxx.vercel.app/pitch
   - See hero stat (live match rate)
   - Read elevator pitch
   - Click CTA to "Launch live console"
   
2. Redirected to /razorpay
   - See "Generate test payment" button
   - Click it, watch match-rate update in real time
   
3. Navigate to /accuracy
   - See F1 trend line and confusion matrix
   - Understand the precision/recall claim
   
4. Navigate to /audit
   - See immutable event log
   - Download a PDF report
   
5. Verify read-only access
   - Cannot create or modify anything
   - Can only view and download
```

**Expected outcome**: Evaluator understands:
- What the product does (reconciliation)
- That it works against live data (Razorpay test mode)
- That it measures accuracy (golden set benchmark)
- That it's audit-proof (immutable log)

All without any explanation or narration.

---

## TROUBLESHOOTING QUICK REFERENCE

### API Won't Start

```bash
# Check logs
railway logs

# Common issues:
# 1. DATABASE_URL missing or invalid
#    → Verify Railway PostgreSQL connection string in env
# 2. REDIS_URL missing
#    → Verify Railway Redis connection string in env
# 3. RAZORPAY_MODE not "test"
#    → Set RAZORPAY_MODE=test explicitly
# 4. Migration not applied
#    → Run: railway run python -m alembic upgrade head
```

### Worker Won't Process Tasks

```bash
# Check logs
railway logs

# Common issues:
# 1. Redis not connected
#    → Verify REDIS_URL in Railway env
# 2. celery_app configuration wrong
#    → Check api/worker.py has correct broker/backend
# 3. Task module not imported
#    → api.tasks must be in celery_app.conf.imports
```

### Frontend Can't Reach API

```bash
# Check CORS configuration
# CORS_ORIGINS must include the Vercel domain

railway env:set CORS_ORIGINS=https://web-xxxx.vercel.app

# Or multiple origins (space-separated):
railway env:set CORS_ORIGINS="https://web-xxxx.vercel.app https://localhost:3000"
```

### Webhook Not Arriving

```bash
# 1. Verify Razorpay webhook URL is correct
#    → Must be: https://api-xxxx.railway.app/api/v1/webhooks/razorpay
# 2. Verify RAZORPAY_WEBHOOK_SECRET matches Razorpay dashboard
# 3. Check logs for webhook delivery:
#    → railway logs | grep "webhook"
# 4. Test webhook manually from Razorpay dashboard
```

---

## ROLLBACK PROCEDURE (If Needed)

### Rollback API

```bash
# Git history
git log --oneline

# Rollback to previous commit
git revert <commit-sha>

# Or force rollback
git reset --hard <commit-sha>

# Redeploy
git push origin main

# Railway will auto-redeploy
railway status  # Watch deployment progress
```

### Rollback Database

```bash
# Rollback to previous migration
railway run python -m alembic downgrade -1

# Or go back multiple migrations
railway run python -m alembic downgrade -3

# Verify
railway run python -m alembic current
```

### Rollback Frontend

```bash
# Vercel keeps deployment history
# In Vercel dashboard: Deployments → Previous Version → Redeploy
# Or:
vercel --prod  # Redeploy latest main
```

---

## POST-DEPLOYMENT MONITORING

### Health Checks (Set Up Monitoring)

```bash
# 1. API health endpoint (every 5 minutes)
https://api-xxxx.railway.app/health

# 2. Celery worker connection (every 30 minutes)
celery -A api.worker inspect ping

# 3. Database connectivity (daily)
railway run python -c "from sqlalchemy import text; \
  from api.db import SessionLocal; \
  async with SessionLocal() as s: \
    await s.execute(text('SELECT 1'))"

# 4. Redis connectivity (daily)
redis-cli -u redis://... PING
```

### Logs

```bash
# Tail API logs
railway logs api

# Tail Worker logs
railway logs worker

# Tail PostgreSQL logs
railway logs postgres

# Tail Redis logs
railway logs redis

# Export logs (for analysis)
railway logs --follow > api.log
```

### Performance Metrics

Monitor in Railway/Vercel dashboards:
- CPU usage
- Memory usage
- Request latency
- Error rate
- Task queue depth (Celery)

---

## SUMMARY

| Phase | Status | Command/Link |
|-------|--------|--------------|
| **Code Freeze** | ✅ Complete | `git push origin main` |
| **Railway Setup** | ⏳ Next | `railway init` |
| **Database** | ⏳ Next | `railway run python -m alembic upgrade head` |
| **API Deploy** | ⏳ Next | `railway deploy` |
| **Worker Deploy** | ⏳ Next | `railway up --cmd "celery..."` |
| **Frontend Deploy** | ⏳ Next | `vercel --prod` |
| **Razorpay Webhook** | ⏳ Next | Razorpay dashboard config |
| **Smoke Tests** | ⏳ Next | 5-min walkthrough |
| **Production Ready** | ⏳ Next | After all tests pass |

---

**Deployment Guide Version**: 1.0  
**Last Updated**: 2026-09-05  
**Status**: Ready for Deployment
