# Admin Statistics and User Tracking

This document details the admin tracking capabilities, dashboard metrics, local development URLs, and environment configuration.

## Overview

Platform administrators require aggregates on sign-up rates and feedback trends to track overall activity. This is implemented via a secure, admin-only panel at `/admin/stats` and endpoints inside FastAPI.

## Security Controls

1.  **Email Allowlist:** Only users whose email is configured in `ADMIN_EMAILS` (backend) and `VITE_ADMIN_EMAILS` (frontend) are granted access.
2.  **Server Verification:** The backend verifies user JWTs and checks their email domain against the allowlist before returning data.
3.  **Admin-Only User Details:** User emails, names, avatars, and activity details are returned only from admin endpoints after backend token verification and admin email allowlist checks.
4.  **Non-Admin Protection:** Non-admin users receive `403`; missing or invalid sessions receive `401`.

## Admin Endpoints

*   `GET /api/v1/admin/user-count`: Returns active users totals, today's sign-ups, and weekly sign-ups.
*   `GET /api/v1/admin/stats`: Returns user metrics, latest signups, recent users, enriched recent feedback, and feedback totals.
*   `GET /api/v1/admin/feedback`: Returns filtered feedback issues enriched with submitter profile details.
*   `POST /api/v1/auth/sync-profile`: Authenticated profile sync fallback. The user id is derived from the bearer token, not from frontend input.

## Supabase Web Dashboard Verification

Supabase CLI migrations are the primary setup path:

```bash
npx supabase login
npx supabase link --project-ref YOUR_PROJECT_REF
npx supabase db push
npx supabase gen types typescript --linked --schema public > frontend/src/types/supabase.ts
```

If Total Users shows `0` even though users have signed in, run the root-level `supabase_admin_dashboard_fix.sql` in the Supabase SQL Editor as a manual fallback. Existing Auth users may need to be backfilled into `public.user_profiles` if they signed in before the trigger existed or before it was corrected.

Use these queries in the Supabase Web Dashboard SQL Editor:

```sql
select count(*) as total_users
from public.user_profiles;
```

```sql
select email, full_name, provider, first_seen_at, last_seen_at
from public.user_profiles
order by first_seen_at desc;
```

```sql
select f.title, f.category, f.status, f.email, p.full_name, f.created_at
from public.feedback_issues f
left join public.user_profiles p on p.id = f.user_id
order by f.created_at desc;
```

```sql
select date(first_seen_at) as signup_date, count(*) as signups
from public.user_profiles
group by date(first_seen_at)
order by signup_date desc;
```

## Local Setup & Configuration

For local development:
*   **Frontend Development Port:** Use `http://localhost:5173`
*   **Backend Server Port:** Use `http://localhost:8000` (not `http://0.0.0.0:8000`, which is the bind address).

### Required Environment Variables

#### Frontend Configuration (`frontend/.env`)
```env
VITE_API_URL=http://localhost:8000/api/v1
VITE_SUPABASE_URL=https://your-supabase-project.supabase.co
VITE_SUPABASE_PUBLISHABLE_KEY=your-publishable-key
VITE_SUPABASE_ANON_KEY=your-anon-key
VITE_APP_URL=http://localhost:5173
VITE_ADMIN_EMAILS=routsoumyajit18@gmail.com,soumyajitrout24@gmail.com
```

#### Backend Configuration (`backend/.env`)
```env
SUPABASE_URL=https://your-supabase-project.supabase.co
SUPABASE_ANON_KEY=your-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
ADMIN_EMAILS=routsoumyajit18@gmail.com,soumyajitrout24@gmail.com
GOOGLE_AUTH_ENABLED=true
```

## Production Notes

- Admin stats are served by the Railway backend and require a Supabase access token from the Vercel frontend.
- Vercel `VITE_API_URL` must point to the Railway backend `/api/v1` URL.
- Railway `CORS_ORIGINS` must include `https://smart-stock18.vercel.app`.
- `ADMIN_EMAILS` must be configured consistently in Railway and Vercel.
