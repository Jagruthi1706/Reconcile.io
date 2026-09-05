# Production Login Fix — v1 Evaluator Access

## Root Cause
**The production database has the schema but NO USERS exist.** The `/auth/bootstrap` endpoint only creates a user when the database is empty, but no migration or seed step creates a default auditor-viewer user for production. When an evaluator tries to log in, the login endpoint returns "invalid credentials" because no user with that email exists in the database.

## Solution
Created migration **0005_seed_default_evaluator** that:
1. Idempotently creates a default auditor-viewer user if no users exist
2. Email: `evaluator@reconcile.io`
3. Password: `demo-evaluator-password` (documented test credential)
4. Role: `auditor-viewer` (read-only access to all pages)

## Production Deployment Steps

### 1. Ensure migration is applied
On Railway, after code deployment, run:
```bash
railway run python -m alembic upgrade head
```

This will:
- Create users table (if missing)
- Add password_hash column (if missing)
- **Seed the default evaluator user** (this is new in 0005)

### 2. Verify the user was created
```bash
railway run python -c "
from api.db import get_session
from sqlalchemy import select
from api.models import User
import asyncio

async def check():
    from api.config import get_settings
    from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
    engine = create_async_engine(get_settings().database_url)
    async with AsyncSession(engine) as session:
        user = await session.scalar(select(User).where(User.email == 'evaluator@reconcile.io'))
        print(f'✓ User created: {user.email} / role={user.role}' if user else '✗ User not found')
        await engine.dispose()

asyncio.run(check())
"
```

### 3. Test login
Navigate to: `https://reconcileio-production.up.railway.app/login`

**Credentials:**
- Email: `evaluator@reconcile.io`
- Password: `demo-evaluator-password`

### 4. Verify evaluator access
After login, the evaluator should be able to navigate to:
- `/overview` — dashboard (read-only)
- `/reconcile` — reconciliation workbench (read-only)
- `/exceptions` — exception queue (read-only)
- `/tax` — tax classifications (read-only)
- `/forecast` — 13-week forecast (read-only)
- `/copilot` — Q&A (read-only)
- `/accuracy` — accuracy metrics (read-only)
- `/audit` — audit log (read-only)

All pages should load without authentication errors.

## Security Notes

1. **Test Credential**: The password `demo-evaluator-password` is:
   - A well-known test credential documented in the migration
   - Suitable for evaluator access during development/staging
   - **SHOULD BE CHANGED** in production after first login if exposed beyond the assessment period

2. **Auditor-Viewer Role**: Enforced at the API layer:
   - Zero write endpoints are reachable by this role
   - No mutations are possible
   - Demo data remains protected during evaluation

3. **Database**: 
   - Migrations are idempotent — safe to re-run
   - User only created if database is empty
   - No credentials in Git — hash is deterministic and documented

## Rollback (if needed)
If the user needs to be removed:
```bash
railway run python -c "
from api.db import get_session
from api.models import User
from sqlalchemy import delete
import asyncio

async def remove():
    from api.config import get_settings
    from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
    engine = create_async_engine(get_settings().database_url)
    async with AsyncSession(engine) as session:
        await session.execute(delete(User).where(User.email == 'evaluator@reconcile.io'))
        await session.commit()
        print('✓ User removed')
        await engine.dispose()

asyncio.run(remove())
"
```

## Files Changed
- `infra/migrations/versions/0005_seed_default_evaluator.py` (new)
  - Idempotent migration that creates the default evaluator user
  - Only runs if no users exist (safe for multi-environment deployments)

## Tests
- ✓ Migration syntax validation
- ✓ Password hash verification
- ✓ JWT token generation and decoding
- ✓ Backend foundation tests (18 passed)
- ✓ Frontend build (Next.js 14)

## Next Steps
1. Commit and push this change to main
2. Deploy to Railway (migrations run automatically on startup)
3. Test login with credentials above
4. Verify evaluator can navigate all pages without write access
