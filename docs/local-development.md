# Local Development

Run the backend and frontend separately:

```powershell
python run.py
Set-Location frontend
npm run dev
Set-Location ..
```

Local frontend configuration:

```env
VITE_API_URL=http://localhost:8000/api/v1
VITE_SUPABASE_URL=your_supabase_url
VITE_SUPABASE_PUBLISHABLE_KEY=your_supabase_publishable_key
VITE_APP_URL=http://localhost:5173
VITE_ADMIN_EMAILS=routsoumyajit18@gmail.com,soumyajitrout24@gmail.com
```

Local backend AI configuration:

```env
APP_ENV=development
AI_PROVIDER=groq
GROQ_API_KEY=your_groq_api_key
DEFAULT_GROQ_API_KEY=your_groq_api_key
AI_MODEL=llama-3.1-8b-instant
AI_REQUEST_TIMEOUT_SECONDS=45
```

Ollama is local-development only and must be explicitly configured on the backend:

```env
APP_ENV=development
AI_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
```

The browser never calls AI providers directly and never stores provider API keys. Ask AI and AI Report Generator call FastAPI routes under `/api/v1/ai`.
