# DEPLOYMENT QUICK REFERENCE CARD
**Reconcile.io v1.0** | GitHub → Railway → Vercel

---

## 🚀 DEPLOYMENT SEQUENCE (TL;DR)

```bash
# 1. PREPARE
cd /path/to/reconcile_io
git push origin main

# 2. RAILWAY API
railway login
railway init  # Create project
railway add   # PostgreSQL
railway add   # Redis

# 3. CONFIGURE RAILWAY ENV
railway env:set RAZORPAY_KEY_ID=<value>
railway env:set RAZORPAY_KEY_SECRET=<value>
railway env:set RAZORPAY_WEBHOOK_SECRET=<value>
railway env:set JWT_SECRET=<secure-random>
railway env:set APP_ENV=production
railway env:set CORS_ORIGINS=https://web-xxxx.vercel.app
railway env:set NEXT_PUBLIC_API_BASE_URL=https://api-xxxx.railway.app/api/v1

# 4. MIGRATE & SEED
railway run python -m alembic upgrade head
railway run python data/seed/seed.py

# 5. DEPLOY SERVICES
railway deploy  # API
railway up --cmd "celery -A api.worker celery_app worker --loglevel=info"  # Worker

# 6. VERCEL FRONTEND
cd apps/web
vercel --prod
vercel env:set NEXT_PUBLIC_API_BASE_URL https://api-xxxx.railway.app/api/v1 --prod

# 7. RAZORPAY WEBHOOK (Dashboard)
URL: https://api-xxxx.railway.app/api/v1/webhooks/razorpay
Events: payment.captured, settlement.processed, refund.processed
Secret: (matches RAZORPAY_WEBHOOK_SECRET)

# 8. SMOKE TESTS
curl https://api-xxxx.railway.app/health
Open https://web-xxxx.vercel.app/pitch
```

---

## 📋 REQUIRED ENVIRONMENT VARIABLES

| Variable | Value | Secret? |
|----------|-------|---------|
| `APP_ENV` | `production` | No |
| `DATABASE_URL` | Railway PostgreSQL (auto) | Yes |
| `REDIS_URL` | Railway Redis (auto) | Yes |
| `JWT_SECRET` | `python -c "import secrets; print(secrets.token_urlsafe(32))"` | Yes |
| `RAZORPAY_KEY_ID` | `rzp_test_xxxxx` | Yes |
| `RAZORPAY_KEY_SECRET` | Dashboard → API Keys | Yes |
| `RAZORPAY_WEBHOOK_SECRET` | Dashboard → Webhooks | Yes |
| `RAZORPAY_MODE` | `test` (hardcoded) | No |
| `CORS_ORIGINS` | `https://web-xxxx.vercel.app` | No |
| `NEXT_PUBLIC_API_BASE_URL` | `https://api-xxxx.railway.app/api/v1` | No |
| `ANTHROPIC_API_KEY` | (optional) | Yes |
| `GEMINI_API_KEY` | (optional) | Yes |

---

## 🔧 BUILD/START COMMANDS

### API (Railway)
```bash
# Build (automatic via Dockerfile.api)
# Start (automatic)
uvicorn api.main:app --host 0.0.0.0 --port 8000
# Health: curl https://api-xxxx.railway.app/health
```

### Worker (Railway)
```bash
# Build (same Dockerfile.api)
# Start
celery -A api.worker celery_app worker --loglevel=info
```

### Frontend (Vercel)
```bash
# Build (automatic)
pnpm install --frozen-lockfile && pnpm build
# Start (automatic)
pnpm start
```

---

## 🗄️ DATABASE COMMANDS

```bash
# Apply all migrations
railway run python -m alembic upgrade head

# Check current migration
railway run python -m alembic current
# Expected: 0004_settlement_lag

# Verify heads
railway run python -m alembic heads
# Expected: 0004_settlement_lag (head)

# Seed demo data (optional)
railway run python data/seed/seed.py
```

---

## 🧪 SMOKE TESTS (5 MIN)

```bash
# 1. API Health
curl https://api-xxxx.railway.app/health
# Expected: {"status": "ok"}

# 2. Frontend Loads
Open: https://web-xxxx.vercel.app/pitch

# 3. Bootstrap Initial User
curl -X POST https://api-xxxx.railway.app/api/v1/auth/bootstrap \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@example.com", "password": "pwd", "role": "controller"}'

# 4. Login
curl -X POST https://api-xxxx.railway.app/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@example.com", "password": "pwd"}'
# Copy access_token

# 5. Get Ledger Lines
curl https://api-xxxx.railway.app/api/v1/ledger/lines \
  -H "Authorization: Bearer <token>"

# 6. Test Razorpay Test-Payment
curl -X POST https://api-xxxx.railway.app/api/v1/razorpay/test-payment \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"amount": 10000, "currency": "INR", "receipt": "test-001"}'

# 7. Navigate All 11 Pages
/pitch, /, /reconcile, /exceptions, /tax, /forecast, /copilot, /razorpay, /accuracy, /audit, /settings

# 8. Export PDF
curl -X POST https://api-xxxx.railway.app/api/v1/export/pdf \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"report_type": "board"}' > report.pdf
```

---

## 🔐 SECRET VALUES (DO NOT COMMIT)

```bash
# Generate JWT_SECRET
python -c "import secrets; print(secrets.token_urlsafe(32))"

# From Razorpay Dashboard:
# Settings → API Keys → Test Key ID & Secret
# Settings → Webhooks → Webhook Secret

# From Anthropic (optional):
# API key from console.anthropic.com

# From Google (optional):
# API key from Google Cloud Console
```

---

## ⚠️ COMMON PITFALLS

| Issue | Fix |
|-------|-----|
| **API won't start** | Check DATABASE_URL & REDIS_URL in Railway env |
| **Worker won't run tasks** | Verify REDIS_URL is set; check logs for connection errors |
| **Frontend can't reach API** | Update CORS_ORIGINS in Railway env to match Vercel domain |
| **Webhook not arriving** | Verify URL is correct, secret matches, test from Razorpay dashboard |
| **RAZORPAY_MODE violation** | Ensure it's hardcoded to "test" in app |
| **Migrations not applied** | Run: `railway run python -m alembic upgrade head` |
| **Frontend sees 404 on API calls** | Verify NEXT_PUBLIC_API_BASE_URL in Vercel env |

---

## 🔄 ROLLBACK

```bash
# Code
git revert <commit-sha>
git push origin main

# Database
railway run python -m alembic downgrade -1

# Frontend
vercel --prod  # Redeploy latest
```

---

## 📊 MONITORING

```bash
# API Health (every 5 min)
curl https://api-xxxx.railway.app/health

# Worker Status
railway logs | grep "connected"

# Database Connectivity
railway run python -m alembic current

# Export Logs
railway logs --follow > debug.log
```

---

## ✅ PRE-DEPLOYMENT CHECKLIST

- [ ] Code is committed: `git status` shows clean
- [ ] Tests pass: `pytest tests/ -q` → 57 passed
- [ ] Frontend builds: `pnpm build` → ✓ Compiled
- [ ] Migrations ready: `alembic heads` → 0004_settlement_lag
- [ ] Railway project created: `railway status` → services listed
- [ ] Environment variables set: `railway env:list` → all present
- [ ] Razorpay credentials available: Dashboard open
- [ ] JWT_SECRET generated: Secure random 32-byte value
- [ ] Vercel project linked: Domain assigned
- [ ] CORS_ORIGINS configured: Matches Vercel domain
- [ ] API_BASE_URL set: Points to Railway API

---

## 📞 SUPPORT

**Logs**: `railway logs` (Real-time tail)  
**Docs**: See DEPLOYMENT_GUIDE.md (Full reference)  
**Health**: `curl https://api-xxxx.railway.app/health`  
**Dashboard**: Railway → Settings → Deployments  

---

**Last Updated**: 2026-09-05  
**Status**: Code Freeze ✅ Ready for Deployment
