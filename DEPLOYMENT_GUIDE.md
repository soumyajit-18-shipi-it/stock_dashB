# Deployment Guide

## Architecture Summary
- **Frontend:** Static React site (Vite).
- **Backend:** Python FastAPI server (Uvicorn).
- **Database:** Supabase (SaaS).

## Deployment Platforms

### 1. Backend (Railway)
- Deployed via `railway.json` and `nixpacks.toml`.
- **Build Command:** Installs Python 3.12 and `requirements.txt`.
- **Start Command:** `python main.py`.
- **Critical Config:** `CORS_ORIGINS` must include the frontend URL.

### 2. Frontend (Vercel)
- **Build Command:** `npm run build`.
- **Output Directory:** `dist`.
- **Rewrites (`vercel.json`):**
  - Proxies `/api/v1/*` to the Railway backend URL to avoid CORS and simplify client-side configuration.

## Environment Variables

### Backend (`.env`)
- `SUPABASE_URL`: Supabase project URL.
- `SUPABASE_SERVICE_ROLE_KEY`: Service key for elevated database access.
- `FINNHUB_API_KEY`: For company profile data.
- `GROQ_API_KEY`: Default provider for AI analysis.

### Frontend (`.env.local`)
- `VITE_API_URL`: Points to the backend (or the Vercel proxy).
- `VITE_SUPABASE_URL` / `VITE_SUPABASE_ANON_KEY`: For direct client-side database interactions.

## Build Steps
1. **Database:** Run Supabase migrations.
2. **Backend:** Push to Railway (triggers Nixpacks build).
3. **Frontend:** Push to Vercel (triggers Vite build).
