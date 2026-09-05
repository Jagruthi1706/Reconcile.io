# RAILWAY & VERCEL DEPLOYMENT UI WALKTHROUGH
**Step-by-Step Visual Guide**

---

## PART 1: RAILWAY.APP SETUP

### Step 1.1: Create Railway Account & Project

**Navigate**: https://railway.app/dashboard  
**If new account**: Click "Create Account" → OAuth with GitHub

**In Dashboard**:
```
┌─ Dashboard
│  └─ New Project
│     └─ Click "+ New Project"
│        └─ Fill in:
│           ├─ Project Name: reconcile-io-api
│           └─ Click "Create"
└─ Project created
   └─ You're now in the project canvas
```

**Expected**: Empty canvas with "+" buttons to add services

---

### Step 1.2: Add PostgreSQL Service

**In Project Canvas**:
```
┌─ Click "+ Add Service"
│  ├─ "Create New"
│  │  └─ "PostgreSQL"
│  └─ Railway provisions PostgreSQL 15
│     └─ Service appears on canvas as "postgres"
│
└─ Configuration auto-complete:
   ├─ DATABASE_URL = postgresql+asyncpg://...
   ├─ POSTGRES_USER = postgres
   └─ POSTGRES_PASSWORD = auto-generated
```

**Verify**: Click on "postgres" service → Environment tab → See DATABASE_URL

---

### Step 1.3: Add Redis Service

**In Project Canvas**:
```
┌─ Click "+ Add Service"
│  ├─ "Create New"
│  │  └─ "Redis"
│  └─ Railway provisions Redis 7
│     └─ Service appears on canvas as "redis"
│
└─ Configuration auto-complete:
   ├─ REDIS_URL = redis://:password@host:port
   └─ REDIS_PASSWORD = auto-generated
```

**Verify**: Click on "redis" service → Environment tab → See REDIS_URL

---

### Step 1.4: Create API Service from GitHub

**In Project Canvas**:
```
┌─ Click "+ Add Service"
│  ├─ "Create New from GitHub repo"
│  └─ Select your GitHub account → Choose "reconcile_io" repo
│     └─ Service appears as "reconcile_io" (or auto-named from repo)
│
└─ Configuration:
   ├─ Build settings (auto-detect):
   │  ├─ Dockerfile: infra/Dockerfile.api ✓
   │  └─ Build context: ./ ✓
   │
   └─ Deployment settings (auto-detect):
      ├─ Port: 8000 ✓
      └─ Start command: (use Dockerfile CMD) ✓
```

**Wait**: Railway builds & deploys (2-3 minutes)  
**Status**: Service goes from "Building" → "Running" (green)

---

### Step 1.5: View Environment Variables (Auto-Set by Railway)

**Click on "reconcile_io" service**:
```
┌─ Service Details Panel
│  ├─ Environment tab
│  │  └─ Read-only variables (auto-set by services):
│  │     ├─ DATABASE_URL (from postgres service)
│  │     ├─ REDIS_URL (from redis service)
│  │     ├─ RAILWAY_PRIVATE_DOMAIN = reconcile_io.railway.internal
│  │     └─ RAILWAY_PUBLIC_DOMAIN = https://reconcile-io-xxxx.railway.app
│  │
│  └─ Edit "Raw Environment Variables"
│     └─ Add custom variables here (see next section)
```

**Note**: Click pencil icon to edit

---

### Step 1.6: Set Required Environment Variables

**In Environment Variables Editor**:

```bash
# Add these (copy-paste each line)
APP_ENV=production
JWT_SECRET=<your-secure-random-value>
RAZORPAY_KEY_ID=rzp_test_<your-key-id>
RAZORPAY_KEY_SECRET=<your-test-secret>
RAZORPAY_WEBHOOK_SECRET=temp-will-update-later
RAZORPAY_MODE=test
CORS_ORIGINS=https://web-xxxx.vercel.app
NEXT_PUBLIC_API_BASE_URL=https://reconcile-io-xxxx.railway.app/api/v1
```

**Steps**:
```
┌─ Click "Raw Environment Variables"
│  └─ Paste above values (replace placeholders)
│     ├─ Each line is KEY=VALUE
│     ├─ NO quotes needed
│     └─ Secrets won't be echoed back
│
└─ Click "Save"
   └─ API service auto-redeploys with new env vars (1 minute)
```

**Verify Deployment**: Status changes to "Running" (green)

---

### Step 1.7: Run Database Migrations

**In Railway CLI** (on your computer):

```bash
cd /path/to/reconcile_io

# Option 1: Using Railway CLI (direct)
railway link  # If not already linked
railway run python -m alembic upgrade head

# Expected output:
# ✓ Executing upgrade scripts
# ✓ Running upgrade 0004_settlement_lag
```

**Or via Dashboard**:
```
┌─ Service: "reconcile_io"
│  └─ Deployments tab
│     └─ Latest deployment
│        └─ Click "Deploy logs"
│           └─ Verify no "ERROR" messages
│
└─ Verify migration via CLI:
   └─ railway run python -m alembic current
      └─ Expected: 0004_settlement_lag
```

---

### Step 1.8: Create Separate Worker Service

**In Project Canvas** (for background jobs):

```
┌─ Click "+ Add Service"
│  └─ "Create New from GitHub repo"
│     └─ Select "reconcile_io" again
│        └─ New service instance for worker
│
└─ Configuration:
   ├─ Name it: "worker" (in settings)
   ├─ Build:
   │  ├─ Dockerfile: infra/Dockerfile.api (same)
   │  └─ Build context: ./
   │
   └─ Deployment:
      ├─ Start command: celery -A api.worker celery_app worker --loglevel=info
      └─ Port: (none needed, no HTTP)
```

**Configuration Steps**:
```
┌─ Click "worker" service
│  └─ Settings tab
│     └─ "Start command" field
│        └─ Replace with: celery -A api.worker celery_app worker --loglevel=info
│
└─ Click "Deploy"
   └─ Service builds & starts (1 minute)
      └─ Expected: Connected to redis, waiting for tasks
```

**Verify Worker**:
```bash
railway logs worker
# Look for: "Connected to redis://..."
# Look for: "mingle: Ready to accept tasks"
```

---

### Step 1.9: Capture Railway API Domain

**In Project Canvas**:
```
┌─ Click on "reconcile_io" service
│  └─ Service details
│     └─ Deployments tab
│        └─ Latest deployment
│           └─ Look for:
│              ├─ "Logs" → Shows public URL
│              ├─ Restart reason: "Started successfully"
│              └─ Or click "Public URL" button
│
└─ URL Format: https://reconcile-io-xxxx.railway.app
   └─ Copy this URL for next steps
```

**Test the URL**:
```bash
curl https://reconcile-io-xxxx.railway.app/health
# Expected: {"status": "ok"}
```

---

## PART 2: VERCEL DEPLOYMENT

### Step 2.1: Create Vercel Account

**Navigate**: https://vercel.com/dashboard  
**If new**: Click "Sign Up" → Select "Continue with GitHub"

---

### Step 2.2: Add Project

**In Vercel Dashboard**:
```
┌─ Click "+ Add New"
│  └─ "Project"
│     └─ "Import Git Repository"
│        └─ Connect GitHub
│           └─ Select "reconcile_io" repo
│
└─ Project imported
   ├─ Auto-detect settings:
   │  ├─ Framework: Next.js ✓
   │  ├─ Root directory: apps/web ✓
   │  └─ Build command: pnpm build ✓
   │
   └─ Click "Deploy"
      └─ Vercel builds & deploys (2-3 minutes)
```

**Watch Progress**:
```
Building → Ready → Deployed
Deployment URL: https://reconcile-io-web.vercel.app (auto-generated)
```

---

### Step 2.3: Configure Environment Variables

**In Vercel Dashboard**:
```
┌─ Project Settings
│  └─ Environment Variables
│     └─ Click "+ Add New"
│        └─ Add these:
│
│           Name: NEXT_PUBLIC_API_BASE_URL
│           Value: https://reconcile-io-xxxx.railway.app/api/v1
│           Environments: ✓ Production ✓ Preview ✓ Development
│           
│           Click "Save"
│
└─ Auto-triggers redeploy with new env var
```

**Verify Redeploy**:
```
Deployments → Latest → Status: Ready
Frontend URL: https://reconcile-io-web.vercel.app
```

---

### Step 2.4: Verify Frontend Loads

**In Browser**:
```
Navigate: https://reconcile-io-web.vercel.app/pitch
Expected:
  ✓ Landing page renders
  ✓ Hero stat visible
  ✓ No console errors (F12 → Console)

Check for CORS errors:
  ✗ If error like "blocked by CORS"
    → Update CORS_ORIGINS in Railway
```

---

### Step 2.5: Update Railway CORS for Vercel Domain

**Go back to Railway Dashboard**:
```
┌─ Project: reconcile-io-api
│  └─ Service: "reconcile_io"
│     └─ Environment tab
│        └─ Edit CORS_ORIGINS
│           └─ Change from: http://localhost:3000
│              To: https://reconcile-io-web.vercel.app
│
└─ Click "Save"
   └─ API service auto-redeploys (1 minute)
```

**Re-verify Frontend**:
```bash
# Open browser console (F12)
# Refresh: https://reconcile-io-web.vercel.app/pitch
# Expected: No CORS errors
```

---

## PART 3: RAZORPAY WEBHOOK CONFIGURATION

### Step 3.1: Login to Razorpay Dashboard

**Navigate**: https://dashboard.razorpay.com  
**Ensure**: Test Mode (toggle visible in top-right)

---

### Step 3.2: Navigate to Webhooks

**In Razorpay Dashboard**:
```
┌─ Settings (left sidebar or gear icon)
│  └─ Webhooks
│     └─ Click "Create Webhook"
```

---

### Step 3.3: Create Webhook

**Fill in webhook form**:

```
┌─ Webhook URL:
│  └─ https://reconcile-io-xxxx.railway.app/api/v1/webhooks/razorpay
│     (Use your Railway API domain)
│
├─ Events to Subscribe:
│  ├─ ☑ payment.captured
│  ├─ ☑ settlement.processed
│  └─ ☑ refund.processed
│
└─ Click "Create"
   └─ Razorpay generates webhook secret
```

**Razorpay generates**:
```
Webhook Secret: whsec_abc123xyz789...
(Copy this value)
```

---

### Step 3.4: Update Railway with Webhook Secret

**Back in Railway CLI**:

```bash
railway env:set RAZORPAY_WEBHOOK_SECRET=whsec_abc123xyz789...
# (Paste the secret from Razorpay)

# Verify it's set:
railway env:list | grep RAZORPAY_WEBHOOK_SECRET
```

**API service auto-redeploys** (1 minute)

---

### Step 3.5: Test Webhook Delivery

**In Razorpay Dashboard**:
```
┌─ Settings → Webhooks
│  └─ Your webhook
│     └─ Click "Test Webhook" button
│
└─ Expected: ✓ Delivered Successfully
```

**Verify in Railway Logs**:
```bash
railway logs api | grep "webhook"
# Expected output:
# INFO: Webhook received from Razorpay
# INFO: Processing payment.captured event
```

---

## PART 4: VERIFICATION WORKFLOW

### Step 4.1: Health Check Sequence

```bash
# 1. API Health
curl https://reconcile-io-xxxx.railway.app/health
# Expected: {"status": "ok"}

# 2. Frontend Loads
Open: https://reconcile-io-web.vercel.app/pitch
# Expected: Page renders, no console errors

# 3. Bootstrap Initial User
curl -X POST https://reconcile-io-xxxx.railway.app/api/v1/auth/bootstrap \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@example.com", "password": "SecurePassword123!", "role": "controller"}'
# Expected: User created, JWT token returned

# 4. Login
curl -X POST https://reconcile-io-xxxx.railway.app/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@example.com", "password": "SecurePassword123!"}'
# Expected: access_token returned

# 5. Get Ledger Lines (empty or seeded)
curl https://reconcile-io-xxxx.railway.app/api/v1/ledger/lines \
  -H "Authorization: Bearer <access_token>"
# Expected: [] or list of seeded data

# 6. Test Razorpay Payment
curl -X POST https://reconcile-io-xxxx.railway.app/api/v1/razorpay/test-payment \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{"amount": 10000, "currency": "INR", "receipt": "test-001"}'
# Expected: Order created, payment captured, settlement pulled

# 7. Worker Processing
railway logs worker | tail -10
# Expected: Task processing logs, no errors
```

---

### Step 4.2: Frontend Navigation Test

```
In Browser:

1. /pitch (Landing)
   ✓ Hero stat visible
   ✓ No console errors

2. /login (Authentication)
   ✓ Login form renders
   ✓ Login succeeds with credentials

3. / (Overview)
   ✓ KPI band loads
   ✓ Match rate displays

4. /reconcile (Workbench)
   ✓ Table renders
   ✓ Side drawer functional

5. /exceptions (Kanban)
   ✓ Columns visible
   ✓ Cards display

6. /tax (Classification)
   ✓ Jurisdiction breakdown shows
   ✓ Review queue visible

7. /forecast (13-week projection)
   ✓ Line chart renders
   ✓ Scenario sliders work

8. /copilot (Chat)
   ✓ Chat UI loads
   ✓ Message send/receive works

9. /razorpay (Live console)
   ✓ Test payment button visible
   ✓ Real-time match rate update works

10. /accuracy (Metrics)
    ✓ F1 trend line displays
    ✓ Confusion matrix visible

11. /audit (Log & export)
    ✓ Event log displays
    ✓ Export buttons (PDF/XLSX/CSV) functional

12. /settings (Admin)
    ✓ Settings form renders
    ✓ Save functionality works
```

---

## PART 5: TROUBLESHOOTING DASHBOARD ISSUES

### API Not Starting

**Check Railway Logs**:
```
┌─ Dashboard: reconcile-io-api project
│  └─ Service: "reconcile_io"
│     └─ Deployments tab
│        └─ Latest deployment
│           └─ "Logs" button
│              └─ Watch for errors:
│                 ├─ ✗ DATABASE_URL not set
│                 ├─ ✗ REDIS_URL not set
│                 ├─ ✗ RAZORPAY_MODE not "test"
│                 └─ ✗ Missing migration
│
└─ Fix: Set environment variables or run migration
```

**From CLI**:
```bash
railway logs api
# Search for ERROR or CRITICAL lines
```

---

### Frontend Can't Reach API

**Check Browser Console** (F12):
```
Look for error like:
  "Cross-Origin Request Blocked:
   https://reconcile-io-xxxx.railway.app/api/v1/...
   (Reason: CORS header 'Access-Control-Allow-Origin' missing)"
```

**Fix**:
```
1. Go to Railway Dashboard
2. Service: "reconcile_io"
3. Environment Variables
4. Find: CORS_ORIGINS
5. Change to: https://reconcile-io-web.vercel.app
6. Save → API redeploys
```

---

### Worker Not Processing Tasks

**Check Railway Logs**:
```bash
railway logs worker
# Look for:
# ✓ "Connected to redis://..."
# ✓ "mingle: Ready to accept tasks"
# ✗ Any ERROR or CRITICAL messages
```

**If logs show errors**:
```
1. Verify REDIS_URL is set in environment
2. Verify Redis service is running (check status)
3. Restart worker:
   - Dashboard → worker service → Settings → Restart
```

---

### Webhook Not Arriving

**Check Razorpay Dashboard**:
```
1. Settings → Webhooks → Your webhook
2. Click "Recent Events" tab
3. Look for failed deliveries
4. Check:
   - URL is correct
   - Secret matches RAZORPAY_WEBHOOK_SECRET
```

**Test Manually**:
```
1. Click "Test" button in Razorpay
2. Expected: ✓ Delivered successfully
3. Check Railway logs:
   - railway logs api | grep webhook
   - Should see webhook received message
```

---

## PART 6: FINAL DEPLOYMENT STATUS

### Create a Status Document

**Save this for record**:

```markdown
# DEPLOYMENT COMPLETE ✅

## Services Status

| Service | Status | URL | Notes |
|---------|--------|-----|-------|
| API | 🟢 Running | https://reconcile-io-xxxx.railway.app | Port 8000 |
| Worker | 🟢 Running | (internal) | Celery connected |
| Database | 🟢 Running | (Railway managed) | PostgreSQL 15 |
| Redis | 🟢 Running | (Railway managed) | Redis 7 |
| Frontend | 🟢 Deployed | https://reconcile-io-web.vercel.app | Next.js |

## Environment Variables

- [x] API_ENV=production
- [x] JWT_SECRET=set
- [x] RAZORPAY_*=set
- [x] CORS_ORIGINS=set
- [x] NEXT_PUBLIC_API_BASE_URL=set

## Integrations

- [x] Razorpay webhook configured
- [x] Webhook secret verified
- [x] Webhook test successful

## Final Checks

- [x] API health endpoint responding
- [x] Frontend loads without errors
- [x] Authentication works
- [x] Razorpay test-payment works
- [x] Worker processes tasks
- [x] All pages render

## Go-Live Date

Deployment Date: ___________
Deployed By: ___________
Verified By: ___________

Status: 🎉 PRODUCTION READY
```

---

**Next Steps**: See DEPLOYMENT_EXECUTION_CHECKLIST.md for final verification steps

---

**Last Updated**: 2026-09-05  
**Status**: Ready for Deployment
