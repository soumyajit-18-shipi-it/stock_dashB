# Deployment

Production uses Railway for the FastAPI backend and Vercel for the Vite frontend.

## Railway Backend

Railway starts the backend with `python run.py`. `run.py` binds to `0.0.0.0` and reads the `PORT` environment variable injected by Railway.

Required Railway variables:

```env
APP_ENV=production
SUPABASE_URL=https://baiveavufaizzlsftpnz.supabase.co
SUPABASE_ANON_KEY=your_supabase_anon_key
SUPABASE_SERVICE_ROLE_KEY=your_supabase_service_role_key
ADMIN_EMAILS=routsoumyajit18@gmail.com,soumyajitrout24@gmail.com
GOOGLE_AUTH_ENABLED=true
FRONTEND_URL=https://smart-stock18.vercel.app
CORS_ORIGINS=https://smart-stock18.vercel.app,http://localhost:5173,http://localhost:5174
AI_PROVIDER=groq
GROQ_API_KEY=your_groq_api_key
DEFAULT_GROQ_API_KEY=your_groq_api_key
AI_MODEL=llama-3.1-8b-instant
AI_REQUEST_TIMEOUT_SECONDS=45
FINNHUB_API_KEY=your_finnhub_api_key
```

Do not set AI provider keys in Vercel or the frontend. Ask AI and AI Report Generator call backend routes only.

Health checks:

```powershell
Invoke-WebRequest https://YOUR-RAILWAY-BACKEND-DOMAIN.up.railway.app/api/v1/health -UseBasicParsing
Invoke-WebRequest https://YOUR-RAILWAY-BACKEND-DOMAIN.up.railway.app/api/v1/health/ai -UseBasicParsing
```

## Vercel Frontend

Vercel builds from the repo root using `cd frontend && npm install && npm run build:pwa`, with output at `frontend/dist`.

Required Vercel variables:

```env
VITE_API_URL=https://YOUR-RAILWAY-BACKEND-DOMAIN.up.railway.app/api/v1
VITE_SUPABASE_URL=https://baiveavufaizzlsftpnz.supabase.co
VITE_SUPABASE_PUBLISHABLE_KEY=your_supabase_publishable_key
VITE_APP_URL=https://smart-stock18.vercel.app
VITE_ADMIN_EMAILS=routsoumyajit18@gmail.com,soumyajitrout24@gmail.com
```

Do not put `SUPABASE_SERVICE_ROLE_KEY`, `GROQ_API_KEY`, `DEFAULT_GROQ_API_KEY`, `OPENAI_API_KEY`, or `OPENROUTER_API_KEY` in Vercel.

## Troubleshooting

- Blank AI message: backend returned zero tokens or an SSE error. The frontend now avoids appending empty assistant messages and shows a retryable error.
- `AI provider is not configured`: set `GROQ_API_KEY` or `DEFAULT_GROQ_API_KEY` in Railway and redeploy.
- `All connection attempts failed`: the backend could not reach the AI provider. Check Railway outbound network, provider status, key validity, and `AI_REQUEST_TIMEOUT_SECONDS`.
- CORS error: include `https://smart-stock18.vercel.app` in Railway `CORS_ORIGINS`.
- Wrong API URL: Vercel `VITE_API_URL` must point to the Railway public domain ending in `/api/v1`, not localhost and not `0.0.0.0`.

Financial questions are answered as educational analysis only. The AI must discuss risks and limitations and should not provide personalized investment advice.
