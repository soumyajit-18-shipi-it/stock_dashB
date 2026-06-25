# Authentication System Documentation

This document explains the authentication architecture, landing gate, local development URLs, database setup, and verification guidelines for the Stock Intelligence Dashboard.

## Architecture

We use **Supabase Auth** integrated with **Google OAuth** for user authentication (including Gmail login).

*   **Google OAuth:** Authentication is processed entirely through Google's OAuth 2.0 flow. No local Gmail API keys are required.
*   **Credentials Security:** The Google Client ID and Client Secret are stored securely within the Supabase Dashboard. They are **never** committed to the repository or sent to the client app.
*   **API Security:** The frontend only uses `VITE_SUPABASE_URL` and `VITE_SUPABASE_ANON_KEY`. It **never** contains or exposes the `SUPABASE_SERVICE_ROLE_KEY`, which is reserved exclusively for the backend to perform elevated queries.
*   **User Synchronization:** When a user logs in, their profile is synchronized to the public `user_profiles` database table using a database trigger.
*   **Backend Token Validation:** Protected FastAPI endpoints expect `Authorization: Bearer <supabase_session.access_token>`. The backend validates that access token with Supabase using the backend-only service-role key. The frontend must never send the anon key, refresh token, service-role key, or an undefined token as the bearer value.
*   **Forced Google Login Gate:** The dashboard forces a beautiful center-aligned Google Sign-In Gate if the user is unauthenticated. The gate displays privacy notices, app capabilities, and config warnings if Supabase variables are missing.
*   **Auth Callback:** The callback redirect handler is mapped to `/auth/callback`.

## User-Owned Data Scope

Login is required before dashboard access. User-owned rows are scoped to the
Supabase authenticated user id (`auth.users.id`):

*   `watchlists.user_id`
*   `search_history.user_id`
*   `predictions.user_id` when predictions are saved
*   `feedback_issues.user_id`

The frontend does not send a manual `user_id`; the backend attaches `user_id`
after token validation. Anonymous users cannot access watchlist or search
history rows.

## Database Setup (Main Path - No CLI Required)

To set up your database schema, you do **not** need the local Supabase CLI. Simply follow these steps using the Supabase Web Dashboard:

1.  Open the file [supabase_setup.sql](file:///C:/Users/soumy/stock_dashB/supabase_setup.sql) in the root of the repository.
2.  Copy the entire content of [supabase_setup.sql](file:///C:/Users/soumy/stock_dashB/supabase_setup.sql).
3.  Go to your **Supabase Web Dashboard**.
4.  Navigate to the **SQL Editor** from the left navigation panel.
5.  Click **New Query** (or **New Empty Query**).
6.  Paste the copied SQL into the editor.
7.  Click **Run** in the bottom right of the editor.

### Optional CLI Database Setup
If you prefer using the Supabase CLI, you can optionally run:
```bash
supabase db push
```

## Web-Dashboard Verification Steps

After running the SQL script in the Supabase Dashboard SQL Editor, verify your database setup is correct:

1.  **Verify Tables Exist:**
    *   Navigate to the **Table Editor** on the left menu.
    *   Confirm that the `public.user_profiles` table exists.
    *   Confirm that the `public.feedback_issues` table exists.
2.  **Verify Users Sync Trigger:**
    *   Once a user completes Google Login, navigate to **Authentication** -> **Users** to confirm they show up in the users list.
    *   Go to **Table Editor** -> `public.user_profiles` to verify their sync profile row has been automatically created.
3.  **Run SQL Test Query:**
    *   Go back to the **SQL Editor**.
    *   Run the following query:
        ```sql
        select count(*) as total_users from public.user_profiles;
        ```
    *   Verify that the query executes successfully and returns the user count.

## Local Development URLs

When running the application locally:
*   **Frontend URL:** [http://localhost:5173](http://localhost:5173)
*   **Backend URL:** [http://localhost:8000](http://localhost:8000) (not the network bind address `http://0.0.0.0:8000`, which is only for network binding and not valid in browser URL inputs).
*   **Backend Docs:** [http://localhost:8000/docs](http://localhost:8000/docs)

Backend logs may show `0.0.0.0:8000` because that is the bind address. Use
`http://localhost:8000` in your browser and set `VITE_API_URL` to
`http://localhost:8000/api/v1`.

## Required Environment Variables

### Frontend (`frontend/.env`)
```env
VITE_API_URL=http://localhost:8000/api/v1
VITE_SUPABASE_URL=https://your-project-ref.supabase.co
VITE_SUPABASE_ANON_KEY=your-supabase-anon-key
VITE_APP_URL=http://localhost:5173
VITE_ADMIN_EMAILS=routsoumyajit18@gmail.com,soumyajitrout24@gmail.com
```

### Backend (`backend/.env`)
```env
SUPABASE_URL=https://your-project-ref.supabase.co
SUPABASE_ANON_KEY=your-supabase-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
ADMIN_EMAILS=routsoumyajit18@gmail.com,soumyajitrout24@gmail.com
GOOGLE_AUTH_ENABLED=true
```

## Manual Supabase Setup

To enable Google/Gmail Sign-In:

1.  **Google Cloud Console Setup:**
    *   Create a project in the Google Cloud Console.
    *   Configure the OAuth Consent Screen.
    *   Create OAuth 2.0 Client Credentials (Web Application).
    *   Copy the Client ID and Client Secret.
    *   Add the Supabase redirect URI (found in the Supabase Dashboard under Auth Settings) to the **Authorized redirect URIs** list in the Google Cloud Console credentials configuration.

2.  **Supabase Dashboard Setup:**
    *   Go to **Authentication** -> **Providers** -> **Google**.
    *   Enable the Google provider.
    *   Paste the Client ID and Client Secret from the Google Cloud Console.
    *   Configure Site URL to your app URL (e.g., `http://localhost:5173`) and add the redirect callback `http://localhost:5173/auth/callback` to the redirect allowlist.
