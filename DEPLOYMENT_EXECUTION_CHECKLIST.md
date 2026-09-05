# DEPLOYMENT EXECUTION CHECKLIST
**Reconcile.io v1.0 → Production**  
**Estimated Duration**: 45 minutes  
**Prepared by**: Engineering Team  
**Status**: CODE FREEZE ✅ Ready for Deployment

---

## 📋 PRE-DEPLOYMENT VERIFICATION (5 minutes)

### Code Readiness

- [ ] **All changes committed**
  ```bash
  cd /path/to/reconcile_io
  git status
  # Expected: nothing to commit, working tree clean
  ```

- [ ] **Latest branch is main**
  ```bash
  git branch -a
  git status | grep "On branch main"
  # Expected: On branch main
  ```

- [ ] **No uncommitted dependencies**
  ```bash
  git log --oneline -5
  # Expected: Recent commits visible
  ```

### Test Suite Validation

- [ ] **Backend tests pass** (57 expected)
  ```bash
  python -m pytest tests/ api/integrations/razorpay/tests/ -q --tb=short
  # Expected: 57 passed, 2 skipped
  ```

- [ ] **Frontend builds** (0 errors expected)
  ```bash
  cd apps/web
  pnpm install --frozen-lockfile
  pnpm build
  # Expected: ✓ Compiled successfully
  ```

- [ ] **No TypeScript errors**
  ```bash
  cd apps/web
  pnpm typecheck
  # Expected: No errors
  ```

- [ ] **No linting issues**
  ```bash
  cd apps/web
  pnpm lint
  # Expected: 0 warnings, 0 errors
  ```

- [ ] **Python compilation check**
  ```bash
  python -m compileall -q api
  # Expected: 0 errors, no output
  ```

### Database Readiness

- [ ] **Migration chain is current**
  ```bash
  python -m alembic heads
  # Expected: 0004_settlement_lag (head)
  ```

- [ ] **No pending migrations**
  ```bash
  python -m alembic current
  # Expected: 0004_settlement_lag (current)
  ```

### Documentation Ready

- [ ] **DEPLOYMENT_GUIDE.md exists and is readable**
- [ ] **DEPLOYMENT_QUICK_REFERENCE.md exists and is readable**
- [ ] **This checklist is printed or available**

---

## 🏗️ RAILWAY INFRASTRUCTURE SETUP (10 minutes)

### Railway Account & Project

- [ ] **Railway CLI installed**
  ```bash
  npm install -g @railway/cli
  # Expected: @railway/cli@latest installed
  ```

- [ ] **Railway authenticated**
  ```bash
  railway login
  # Opens browser for OAuth login
  # Expected: Successfully authenticated
  ```

- [ ] **Railway project created**
  ```bash
  railway init
  # When prompted: "Create a new project"
  # Name: reconcile-io-api
  # Expected: Project created, .railway/config.json present
  ```

- [ ] **Railway status verified**
  ```bash
  railway status
  # Expected: Project name, URL, environment listed
  ```

### Database Service

- [ ] **PostgreSQL 15 service added**
  ```bash
  railway add
  # Select: PostgreSQL
  # Expected: PostgreSQL service created
  ```

- [ ] **PostgreSQL connection available**
  ```bash
  railway status
  # Expected: PostgreSQL service listed with status "running"
  ```

- [ ] **DATABASE_URL captured**
  ```bash
  railway env:list | grep DATABASE_URL
  # Note: This will be auto-set by Railway, copy value for reference
  # Format: postgresql+asyncpg://user:pass@host:5432/dbname
  ```

### Redis Service

- [ ] **Redis 7 service added**
  ```bash
  railway add
  # Select: Redis
  # Expected: Redis service created
  ```

- [ ] **Redis connection available**
  ```bash
  railway status
  # Expected: Redis service listed with status "running"
  ```

- [ ] **REDIS_URL captured**
  ```bash
  railway env:list | grep REDIS_URL
  # Format: redis://:password@host:port/db
  ```

---

## 🔐 ENVIRONMENT VARIABLES CONFIGURATION (10 minutes)

### Gather Required Values

**Before proceeding, have these values ready:**
- [ ] Razorpay KEY_ID (from Dashboard → Settings → API Keys)
- [ ] Razorpay KEY_SECRET (from Dashboard → Settings → API Keys)
- [ ] Razorpay WEBHOOK_SECRET (will be created below)
- [ ] JWT_SECRET (generate new):
  ```bash
  python -c "import secrets; print(secrets.token_urlsafe(32))"
  # Copy the output value
  ```
- [ ] Vercel Frontend Domain (e.g., web-xxxx.vercel.app)
- [ ] Railway API Domain (will be available after deployment)

### Set Application Environment

- [ ] **Set APP_ENV to production**
  ```bash
  railway env:set APP_ENV=production
  ```

- [ ] **Set JWT_SECRET (secure random)**
  ```bash
  railway env:set JWT_SECRET=<value-from-above>
  # Do NOT echo or print this value
  ```

### Set Razorpay Credentials

- [ ] **Set RAZORPAY_KEY_ID**
  ```bash
  railway env:set RAZORPAY_KEY_ID=<your-test-key-id>
  ```

- [ ] **Set RAZORPAY_KEY_SECRET**
  ```bash
  railway env:set RAZORPAY_KEY_SECRET=<your-test-key-secret>
  # Do NOT print this value
  ```

- [ ] **Set RAZORPAY_MODE (hardcoded to test)**
  ```bash
  railway env:set RAZORPAY_MODE=test
  ```

- [ ] **RAZORPAY_WEBHOOK_SECRET (temporary placeholder)**
  ```bash
  railway env:set RAZORPAY_WEBHOOK_SECRET=temporary-will-update-later
  # Will update after creating webhook in Razorpay
  ```

### Set CORS & API URLs (Temporary)

- [ ] **Set CORS_ORIGINS (temporary)**
  ```bash
  railway env:set CORS_ORIGINS=http://localhost:3000
  # Will update after Vercel deployment
  ```

- [ ] **Set NEXT_PUBLIC_API_BASE_URL (temporary)**
  ```bash
  railway env:set NEXT_PUBLIC_API_BASE_URL=http://localhost:8000/api/v1
  # Will update after Railway API deployment
  ```

### Verify Environment Variables Set

- [ ] **Confirm all variables are set**
  ```bash
  railway env:list
  # Expected output shows: APP_ENV, DATABASE_URL, REDIS_URL,
  #   JWT_SECRET, RAZORPAY_*, CORS_ORIGINS, NEXT_PUBLIC_API_BASE_URL
  ```

---

## 💾 DATABASE INITIALIZATION (5 minutes)

### Apply Migrations

- [ ] **Run all pending migrations**
  ```bash
  railway run python -m alembic upgrade head
  # Expected: INFO [alembic.runtime.migration] Running upgrade...
  # INFO [alembic.runtime.migration] Running upgrade 0004_settlement_lag
  ```

- [ ] **Verify final migration**
  ```bash
  railway run python -m alembic current
  # Expected: 0004_settlement_lag
  ```

### Seed Demo Data (Optional)

- [ ] **Run seed script (for demo/staging)**
  ```bash
  railway run python data/seed/seed.py
  # Expected: Seed data inserted
  # Note: Skip for production first deploy; can seed later if needed
  ```

---

## 🚀 API SERVICE DEPLOYMENT (5 minutes)

### Deploy API Service

- [ ] **Connect Railway to GitHub**
  ```bash
  railway connect
  # Provide GitHub token (personal access token with repo permissions)
  # Select your reconcile_io repository
  # Expected: Connected to GitHub
  ```

- [ ] **Deploy API service**
  ```bash
  railway up
  # Uses Dockerfile at: infra/Dockerfile.api
  # Expected: Build logs showing steps 1-11, "Deployment successful"
  ```

- [ ] **Wait for deployment to complete**
  ```bash
  railway status
  # Watch for status change to "running"
  # Takes 2-3 minutes typically
  ```

- [ ] **Capture API service URL**
  ```bash
  railway env:list | grep -i "railway_public_domain"
  # Format: https://api-xxxx.railway.app
  # OR check dashboard for service URL
  ```

### Verify API Service

- [ ] **Test API health endpoint**
  ```bash
  curl https://api-xxxx.railway.app/health
  # Expected: {"status": "ok"}
  # If fails: Check railway logs with: railway logs api
  ```

- [ ] **Verify Swagger docs available**
  ```bash
  curl -s https://api-xxxx.railway.app/docs | head -20
  # Expected: HTML response, FastAPI Swagger UI structure
  ```

- [ ] **Check API logs for errors**
  ```bash
  railway logs api
  # Expected: Startup logs showing "Uvicorn running on 0.0.0.0:8000"
  # No CRITICAL or ERROR messages
  ```

---

## 👷 CELERY WORKER DEPLOYMENT (5 minutes)

### Deploy Worker Service

- [ ] **Create worker service in Railway**
  ```bash
  railway service add worker
  # This adds a new service to the project
  ```

- [ ] **Configure worker build**
  ```bash
  # Worker uses same Dockerfile as API (infra/Dockerfile.api)
  # Railway will auto-detect this
  ```

- [ ] **Set worker start command**
  ```bash
  railway env:set WORKER_CMD="celery -A api.worker celery_app worker --loglevel=info"
  # In Railway dashboard, set the service override to this command
  ```

- [ ] **Deploy worker**
  ```bash
  railway up  # While connected to worker service
  # Expected: Build completes, service starts
  ```

- [ ] **Wait for worker to initialize**
  ```bash
  railway logs worker
  # Watch for: "Connected to redis://..."
  # Expected: "mingle: Calling on_ready() of PoolPool..."
  # Takes 30-60 seconds
  ```

### Verify Worker Connection

- [ ] **Worker connected to broker**
  ```bash
  railway logs worker | grep -i "connected"
  # Expected: Message showing connection to Redis
  ```

- [ ] **Worker ready for tasks**
  ```bash
  railway logs worker | tail -20
  # Expected: No error messages, ready to accept tasks
  ```

---

## 🌐 FRONTEND DEPLOYMENT (Vercel) (10 minutes)

### Prepare Frontend Deployment

- [ ] **Install Vercel CLI**
  ```bash
  npm install -g vercel
  ```

- [ ] **Login to Vercel**
  ```bash
  vercel login
  # Opens browser for OAuth login
  ```

- [ ] **Navigate to frontend directory**
  ```bash
  cd apps/web
  pwd
  # Expected: /path/to/reconcile_io/apps/web
  ```

### Deploy Frontend

- [ ] **Deploy to Vercel**
  ```bash
  vercel --prod
  # Provide project setup:
  #   - Create new project or link existing
  #   - Build settings: (auto-detect) pnpm build
  #   - Output: .next
  # Expected: Deployment URL provided
  ```

- [ ] **Capture Vercel domain**
  ```bash
  vercel env:list
  # Note the production URL (e.g., https://web-xxxx.vercel.app)
  ```

- [ ] **Wait for build to complete**
  ```bash
  # Vercel build takes 2-3 minutes
  # Check Deployments dashboard for progress
  # Expected: "Ready" status
  ```

### Configure Frontend Environment

- [ ] **Set NEXT_PUBLIC_API_BASE_URL on Vercel**
  ```bash
  vercel env:set NEXT_PUBLIC_API_BASE_URL https://api-xxxx.railway.app/api/v1 --prod
  # Use the Railway API domain captured earlier
  ```

- [ ] **Redeploy frontend with new env variable**
  ```bash
  vercel --prod
  # Vercel should auto-redeploy with new env var
  # Expected: New deployment with updated API base URL
  ```

### Verify Frontend

- [ ] **Frontend loads**
  ```bash
  Open: https://web-xxxx.vercel.app/pitch
  # Expected: Landing page renders, hero stat visible
  # Check browser console for errors (F12)
  ```

- [ ] **No API connection errors in console**
  ```bash
  Open DevTools (F12) → Console tab
  # Expected: No CORS errors, no 404s for /api/v1 calls
  # If errors, verify NEXT_PUBLIC_API_BASE_URL is correct
  ```

---

## 🪝 RAZORPAY WEBHOOK CONFIGURATION (5 minutes)

### Create Webhook in Razorpay Dashboard

- [ ] **Login to Razorpay Dashboard**
  ```
  URL: https://dashboard.razorpay.com
  Use test mode (ensure not live mode)
  ```

- [ ] **Navigate to Webhooks**
  ```
  Settings → Webhooks → Add New Webhook
  ```

- [ ] **Configure Webhook URL**
  ```
  Webhook URL: https://api-xxxx.railway.app/api/v1/webhooks/razorpay
  (Use the Railway API domain captured earlier)
  ```

- [ ] **Select Events to Subscribe**
  ```
  ✓ payment.captured
  ✓ settlement.processed
  ✓ refund.processed
  ```

- [ ] **Generate & Copy Webhook Secret**
  ```
  Razorpay will generate a secret
  Copy this secret value
  ```

- [ ] **Update Railway with Webhook Secret**
  ```bash
  railway env:set RAZORPAY_WEBHOOK_SECRET=<webhook-secret-from-razorpay>
  # Do NOT print this value
  ```

- [ ] **Verify CORS & API Configuration**
  ```bash
  railway env:list | grep -E "CORS|RAZORPAY"
  # Expected: All Razorpay variables and CORS_ORIGINS set
  ```

### Test Webhook Delivery

- [ ] **Click "Test Webhook" in Razorpay Dashboard**
  ```
  Settings → Webhooks → Your Webhook → Test
  Expected: Webhook delivered successfully
  ```

- [ ] **Monitor API logs for webhook delivery**
  ```bash
  railway logs api | grep "webhook"
  # Expected: Logs showing webhook received and processed
  ```

---

## ✅ FINAL VERIFICATION & SMOKE TESTS (10 minutes)

### System Health Checks

- [ ] **API service health**
  ```bash
  curl https://api-xxxx.railway.app/health
  # Expected: {"status": "ok"}
  ```

- [ ] **Database connectivity**
  ```bash
  railway run python -c "from sqlalchemy import text; \
    from api.db import SessionLocal; \
    import asyncio; \
    asyncio.run(SessionLocal().execute(text('SELECT 1')))"
  # Expected: (1,) — no errors
  ```

- [ ] **Redis connectivity**
  ```bash
  railway run python -c "import redis; \
    r = redis.from_url('$REDIS_URL'); \
    print(r.ping())"
  # Expected: True
  ```

- [ ] **Worker status**
  ```bash
  railway logs worker | tail -5
  # Expected: No errors, ready to process tasks
  ```

### Authentication Flow

- [ ] **Create initial user (bootstrap)**
  ```bash
  curl -X POST https://api-xxxx.railway.app/api/v1/auth/bootstrap \
    -H "Content-Type: application/json" \
    -d '{
      "email": "admin@example.com",
      "password": "SecurePassword123!",
      "role": "controller"
    }'
  # Expected: {"user": {"email": "admin@example.com", "role": "controller"}, ...}
  # Note: Save this JWT token for next steps
  ```

- [ ] **Perform login**
  ```bash
  curl -X POST https://api-xxxx.railway.app/api/v1/auth/login \
    -H "Content-Type: application/json" \
    -d '{"email": "admin@example.com", "password": "SecurePassword123!"}'
  # Expected: {"access_token": "eyJ...", "token_type": "bearer", "user": {...}}
  # Copy access_token value
  ```

### API Functionality

- [ ] **List ledger lines (empty or seeded)**
  ```bash
  curl https://api-xxxx.railway.app/api/v1/ledger/lines \
    -H "Authorization: Bearer <access_token>"
  # Expected: [] (empty if not seeded) or list of lines
  ```

- [ ] **Test Razorpay test-payment endpoint**
  ```bash
  curl -X POST https://api-xxxx.railway.app/api/v1/razorpay/test-payment \
    -H "Authorization: Bearer <access_token>" \
    -H "Content-Type: application/json" \
    -d '{"amount": 10000, "currency": "INR", "receipt": "test-001"}'
  # Expected: {"id": "order_...", "amount": 10000, ...}
  ```

- [ ] **Verify webhook triggered reconciliation**
  ```bash
  railway logs worker | grep "reconciliation"
  # Expected: Logs showing task execution
  ```

### Frontend Smoke Test

- [ ] **Landing page loads**
  ```bash
  Open: https://web-xxxx.vercel.app/pitch
  # Expected: Hero stat visible, no console errors
  # Check DevTools console (F12) for errors
  ```

- [ ] **Login works**
  ```bash
  Click: "Launch live console" or navigate to /login
  Enter: admin@example.com / SecurePassword123!
  # Expected: Redirect to overview page
  ```

- [ ] **Reconcile page loads**
  ```bash
  Navigate to: /reconcile
  # Expected: Workbench UI renders, possibly empty if no seeded data
  ```

- [ ] **All 11 pages accessible**
  ```bash
  /pitch → ✓
  /       → ✓
  /reconcile → ✓
  /exceptions → ✓
  /tax → ✓
  /forecast → ✓
  /copilot → ✓
  /razorpay → ✓
  /accuracy → ✓
  /audit → ✓
  /settings → ✓
  ```

### Export Functionality

- [ ] **PDF export works**
  ```bash
  curl -X POST https://api-xxxx.railway.app/api/v1/export/pdf \
    -H "Authorization: Bearer <access_token>" \
    -H "Content-Type: application/json" \
    -d '{"report_type": "board"}' > report.pdf
  # Expected: Binary PDF file, Content-Type: application/pdf
  ```

### Role-Based Access Control

- [ ] **Auditor-viewer role read-only**
  ```bash
  # Create auditor-viewer user:
  curl -X POST https://api-xxxx.railway.app/api/v1/auth/bootstrap \
    -H "Content-Type: application/json" \
    -d '{"email": "viewer@example.com", "password": "pwd", "role": "auditor-viewer"}'
  
  # Login as auditor-viewer:
  curl -X POST https://api-xxxx.railway.app/api/v1/auth/login \
    -H "Content-Type: application/json" \
    -d '{"email": "viewer@example.com", "password": "pwd"}'
  
  # Try to create a run (should fail):
  curl -X POST https://api-xxxx.railway.app/api/v1/runs \
    -H "Authorization: Bearer <auditor-token>"
  # Expected: 403 Forbidden
  ```

---

## 🎯 FINAL WALKTHROUGH (5-Minute Scenario)

**Scenario**: Non-technical evaluator viewing the product

- [ ] **Step 1**: Open https://web-xxxx.vercel.app/pitch
  - [ ] Landing page loads
  - [ ] Hero stat displays live match rate
  - [ ] CTA button visible: "Launch live console"

- [ ] **Step 2**: Click CTA → Redirected to /razorpay page
  - [ ] Page renders with "Generate test payment" button
  - [ ] Button clickable

- [ ] **Step 3**: Generate test payment
  - [ ] Button click triggers payment creation
  - [ ] Match rate updates in real time
  - [ ] Toast notification shows success

- [ ] **Step 4**: Navigate to /accuracy page
  - [ ] F1 trend line displays
  - [ ] Confusion matrix visible
  - [ ] "Run Benchmark" button present

- [ ] **Step 5**: Navigate to /audit page
  - [ ] Event log displays
  - [ ] Export buttons (PDF, XLSX, CSV) visible
  - [ ] Download PDF works

- [ ] **Step 6**: Verify read-only access (if logged in as auditor-viewer)
  - [ ] Cannot create or modify anything
  - [ ] Can only view and download

**Expected Outcome**: Evaluator understands:
- What product does (reconciliation)
- That it works with live data (Razorpay)
- That it measures accuracy (golden set benchmark)
- That it's audit-proof (immutable log)

---

## ⚠️ TROUBLESHOOTING QUICK FIXES

| Symptom | Check | Fix |
|---------|-------|-----|
| API won't start | `railway logs api` | Check DATABASE_URL & REDIS_URL set |
| 502 Bad Gateway on API | `curl https://api.../health` | Verify API service is running |
| Frontend can't reach API | Browser console | Verify NEXT_PUBLIC_API_BASE_URL in Vercel |
| CORS errors | Browser console | Update CORS_ORIGINS in Railway to match Vercel domain |
| Webhook not arriving | `railway logs api` | Verify URL and secret in Razorpay dashboard |
| Worker stuck | `railway logs worker` | Restart worker service or check Redis connection |

---

## ✨ SUCCESS CRITERIA

After completing this checklist, verify all criteria:

- [ ] ✅ API responds to `curl https://api-xxxx.railway.app/health`
- [ ] ✅ Frontend loads at https://web-xxxx.vercel.app/pitch
- [ ] ✅ Authentication works (login creates JWT token)
- [ ] ✅ Razorpay test-payment endpoint returns order
- [ ] ✅ Worker processes reconciliation tasks
- [ ] ✅ All 11 frontend pages render without errors
- [ ] ✅ PDF export generates valid file
- [ ] ✅ Auditor-viewer role enforces read-only access
- [ ] ✅ No errors in API logs (railway logs api)
- [ ] ✅ No errors in Worker logs (railway logs worker)
- [ ] ✅ No errors in browser console (F12)
- [ ] ✅ Settlement lag calculated (not 0.00)

**If all criteria met**: 🎉 **DEPLOYMENT SUCCESSFUL** 🎉

---

## 📊 POST-DEPLOYMENT TASKS

- [ ] **Monitor API logs for 24 hours**
  - [ ] Watch for errors
  - [ ] Monitor request latency
  - [ ] Check database query performance

- [ ] **Monitor Celery worker**
  - [ ] Verify tasks are processing
  - [ ] Check for failed tasks
  - [ ] Monitor queue depth

- [ ] **Monitor frontend analytics**
  - [ ] Check user traffic
  - [ ] Monitor error rates
  - [ ] Review console errors from users

- [ ] **Setup alerting** (optional but recommended)
  - [ ] API health endpoint check (5-min interval)
  - [ ] Database connectivity check
  - [ ] Celery worker status check
  - [ ] Error rate thresholds

- [ ] **Daily standup checklist**
  - [ ] All services running
  - [ ] No error spikes
  - [ ] User activity normal
  - [ ] No pending tasks stuck in queue

---

## 📞 SUPPORT CONTACTS

- **Railway Support**: https://railway.app/support
- **Vercel Support**: https://vercel.com/support
- **Razorpay Support**: https://razorpay.com/contact/support
- **Internal Logs**: `railway logs` command
- **Full Guide**: See DEPLOYMENT_GUIDE.md

---

## ✅ SIGN-OFF

**Deployment Executor**: ___________________________  
**Date**: ___________________________  
**Time Started**: ___________________________  
**Time Completed**: ___________________________  
**Any Issues?**: ___________________________  
**Notes**: ___________________________  

---

**Status**: 🟢 Ready for Production  
**Code Freeze**: ✅ In Effect  
**Last Updated**: 2026-09-05
