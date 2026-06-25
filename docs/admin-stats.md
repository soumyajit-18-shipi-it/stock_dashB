# Admin Statistics and User Tracking

This document details the admin tracking capabilities, dashboard metrics, local development URLs, and environment configuration.

## Overview

Platform administrators require aggregates on sign-up rates and feedback trends to track overall activity. This is implemented via a secure, admin-only panel at `/admin/stats` and endpoints inside FastAPI.

## Security Controls

1.  **Email Allowlist:** Only users whose email is configured in `ADMIN_EMAILS` (backend) and `VITE_ADMIN_EMAILS` (frontend) are granted access.
2.  **Server Verification:** The backend verifies user JWTs and checks their email domain against the allowlist before returning data.
3.  **Data Minimization:** No personal information (e.g. user emails list) is exposed via the stats endpoints. Only counts and timestamps are returned.

## Admin Endpoints

*   `GET /api/v1/admin/user-count`: Returns active users totals, today's sign-ups, and weekly sign-ups.
*   `GET /api/v1/admin/stats`: Returns user metrics and feedback totals (including open report counts).
*   `GET /api/v1/admin/feedback`: Returns all feedback issues for inspection.

## Local Setup & Configuration

For local development:
*   **Frontend Development Port:** Use `http://localhost:5173`
*   **Backend Server Port:** Use `http://localhost:8000` (not `http://0.0.0.0:8000`, which is the bind address).

### Required Environment Variables

#### Frontend Configuration (`frontend/.env`)
```env
VITE_API_URL=http://localhost:8000/api/v1
VITE_SUPABASE_URL=https://your-supabase-project.supabase.co
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
