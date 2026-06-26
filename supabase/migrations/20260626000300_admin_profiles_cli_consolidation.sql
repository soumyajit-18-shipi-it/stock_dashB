-- CLI-first consolidation for auth profiles, feedback, and user-scoped app data.
-- Safe for hosted `supabase db push`; do not use `db reset` on production data.

CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE IF NOT EXISTS public.watchlists (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID,
    ticker TEXT NOT NULL,
    name TEXT,
    company_name TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS public.search_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID,
    query TEXT,
    ticker TEXT NOT NULL,
    searched_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS public.predictions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID,
    ticker TEXT NOT NULL,
    model TEXT NOT NULL,
    predicted_price DECIMAL(18, 4),
    actual_price DECIMAL(18, 4),
    confidence DECIMAL(5, 4),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS public.saved_models (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    model_name TEXT UNIQUE NOT NULL,
    file_path TEXT NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

ALTER TABLE public.watchlists
    ADD COLUMN IF NOT EXISTS user_id UUID,
    ADD COLUMN IF NOT EXISTS name TEXT,
    ADD COLUMN IF NOT EXISTS company_name TEXT,
    ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ DEFAULT NOW();

ALTER TABLE public.search_history
    ADD COLUMN IF NOT EXISTS user_id UUID,
    ADD COLUMN IF NOT EXISTS query TEXT,
    ADD COLUMN IF NOT EXISTS searched_at TIMESTAMPTZ DEFAULT NOW();

ALTER TABLE public.predictions
    ADD COLUMN IF NOT EXISTS user_id UUID,
    ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ DEFAULT NOW();

UPDATE public.watchlists
SET ticker = upper(ticker),
    company_name = COALESCE(company_name, name)
WHERE ticker IS NOT NULL;

UPDATE public.search_history
SET ticker = upper(ticker),
    query = COALESCE(query, ticker)
WHERE ticker IS NOT NULL;

DO $$
DECLARE
    constraint_name TEXT;
BEGIN
    FOR constraint_name IN
        SELECT conname
        FROM pg_constraint
        WHERE conrelid = 'public.watchlists'::regclass
          AND contype = 'f'
    LOOP
        EXECUTE format('ALTER TABLE public.watchlists DROP CONSTRAINT IF EXISTS %I', constraint_name);
    END LOOP;

    FOR constraint_name IN
        SELECT conname
        FROM pg_constraint
        WHERE conrelid = 'public.search_history'::regclass
          AND contype = 'f'
    LOOP
        EXECUTE format('ALTER TABLE public.search_history DROP CONSTRAINT IF EXISTS %I', constraint_name);
    END LOOP;

    FOR constraint_name IN
        SELECT conname
        FROM pg_constraint
        WHERE conrelid = 'public.predictions'::regclass
          AND contype = 'f'
    LOOP
        EXECUTE format('ALTER TABLE public.predictions DROP CONSTRAINT IF EXISTS %I', constraint_name);
    END LOOP;
END $$;

ALTER TABLE public.watchlists
    ADD CONSTRAINT watchlists_user_id_fkey
    FOREIGN KEY (user_id) REFERENCES auth.users(id) ON DELETE CASCADE NOT VALID;

ALTER TABLE public.search_history
    ADD CONSTRAINT search_history_user_id_fkey
    FOREIGN KEY (user_id) REFERENCES auth.users(id) ON DELETE CASCADE NOT VALID;

ALTER TABLE public.predictions
    ADD CONSTRAINT predictions_user_id_fkey
    FOREIGN KEY (user_id) REFERENCES auth.users(id) ON DELETE CASCADE NOT VALID;

CREATE TABLE IF NOT EXISTS public.user_profiles (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    email TEXT,
    full_name TEXT,
    avatar_url TEXT,
    provider TEXT DEFAULT 'google',
    first_seen_at TIMESTAMPTZ DEFAULT NOW(),
    last_seen_at TIMESTAMPTZ DEFAULT NOW(),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

ALTER TABLE public.user_profiles
    ADD COLUMN IF NOT EXISTS email TEXT,
    ADD COLUMN IF NOT EXISTS full_name TEXT,
    ADD COLUMN IF NOT EXISTS avatar_url TEXT,
    ADD COLUMN IF NOT EXISTS provider TEXT DEFAULT 'google',
    ADD COLUMN IF NOT EXISTS first_seen_at TIMESTAMPTZ DEFAULT NOW(),
    ADD COLUMN IF NOT EXISTS last_seen_at TIMESTAMPTZ DEFAULT NOW(),
    ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ DEFAULT NOW(),
    ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ DEFAULT NOW();

CREATE TABLE IF NOT EXISTS public.feedback_issues (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES auth.users(id) ON DELETE SET NULL,
    email TEXT,
    category TEXT NOT NULL CHECK (category IN ('feature_request', 'bug_report', 'documentation_issue', 'setup_query', 'development_query')),
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    page_url TEXT,
    screenshot_url TEXT,
    status TEXT DEFAULT 'open' CHECK (status IN ('open', 'in_review', 'planned', 'resolved', 'closed')),
    priority TEXT DEFAULT 'normal' CHECK (priority IN ('low', 'normal', 'high', 'urgent')),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

ALTER TABLE public.feedback_issues
    ADD COLUMN IF NOT EXISTS user_id UUID REFERENCES auth.users(id) ON DELETE SET NULL,
    ADD COLUMN IF NOT EXISTS email TEXT,
    ADD COLUMN IF NOT EXISTS page_url TEXT,
    ADD COLUMN IF NOT EXISTS screenshot_url TEXT,
    ADD COLUMN IF NOT EXISTS status TEXT DEFAULT 'open',
    ADD COLUMN IF NOT EXISTS priority TEXT DEFAULT 'normal',
    ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ DEFAULT NOW(),
    ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ DEFAULT NOW();

CREATE INDEX IF NOT EXISTS idx_watchlists_user_id ON public.watchlists(user_id);
CREATE INDEX IF NOT EXISTS idx_watchlists_ticker ON public.watchlists(ticker);
CREATE UNIQUE INDEX IF NOT EXISTS idx_watchlists_user_ticker_unique ON public.watchlists(user_id, ticker);
CREATE INDEX IF NOT EXISTS idx_search_history_user_id ON public.search_history(user_id);
CREATE INDEX IF NOT EXISTS idx_search_history_ticker ON public.search_history(ticker);
CREATE INDEX IF NOT EXISTS idx_search_history_user_created ON public.search_history(user_id, searched_at DESC);
CREATE INDEX IF NOT EXISTS idx_predictions_ticker ON public.predictions(ticker);
CREATE INDEX IF NOT EXISTS idx_predictions_created_at ON public.predictions(created_at);
CREATE INDEX IF NOT EXISTS idx_predictions_user_created ON public.predictions(user_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_user_profiles_email ON public.user_profiles(email);
CREATE INDEX IF NOT EXISTS idx_user_profiles_created_at ON public.user_profiles(created_at);
CREATE INDEX IF NOT EXISTS idx_user_profiles_first_seen ON public.user_profiles(first_seen_at DESC);
CREATE INDEX IF NOT EXISTS idx_user_profiles_last_seen ON public.user_profiles(last_seen_at DESC);
CREATE INDEX IF NOT EXISTS idx_feedback_user_id ON public.feedback_issues(user_id);
CREATE INDEX IF NOT EXISTS idx_feedback_email ON public.feedback_issues(email);
CREATE INDEX IF NOT EXISTS idx_feedback_category ON public.feedback_issues(category);
CREATE INDEX IF NOT EXISTS idx_feedback_status ON public.feedback_issues(status);
CREATE INDEX IF NOT EXISTS idx_feedback_created_at ON public.feedback_issues(created_at);

ALTER TABLE public.watchlists ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.search_history ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.predictions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.saved_models ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.user_profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.feedback_issues ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "allow_all_watchlists" ON public.watchlists;
DROP POLICY IF EXISTS "allow_all_search_history" ON public.search_history;
DROP POLICY IF EXISTS "allow_all_predictions" ON public.predictions;
DROP POLICY IF EXISTS "allow_all_saved_models" ON public.saved_models;
DROP POLICY IF EXISTS "allow_all_users" ON public.users;
DROP POLICY IF EXISTS "auth_watchlists" ON public.watchlists;
DROP POLICY IF EXISTS "auth_search_history" ON public.search_history;
DROP POLICY IF EXISTS "auth_predictions" ON public.predictions;
DROP POLICY IF EXISTS "auth_saved_models" ON public.saved_models;
DROP POLICY IF EXISTS "auth_users" ON public.users;
DROP POLICY IF EXISTS "select_own_watchlists" ON public.watchlists;
DROP POLICY IF EXISTS "insert_own_watchlists" ON public.watchlists;
DROP POLICY IF EXISTS "update_own_watchlists" ON public.watchlists;
DROP POLICY IF EXISTS "delete_own_watchlists" ON public.watchlists;
DROP POLICY IF EXISTS "select_own_search_history" ON public.search_history;
DROP POLICY IF EXISTS "insert_own_search_history" ON public.search_history;
DROP POLICY IF EXISTS "delete_own_search_history" ON public.search_history;
DROP POLICY IF EXISTS "select_predictions" ON public.predictions;
DROP POLICY IF EXISTS "insert_predictions" ON public.predictions;
DROP POLICY IF EXISTS "select_own_predictions" ON public.predictions;
DROP POLICY IF EXISTS "insert_own_predictions" ON public.predictions;
DROP POLICY IF EXISTS "select_saved_models" ON public.saved_models;
DROP POLICY IF EXISTS "Users can read own profile" ON public.user_profiles;
DROP POLICY IF EXISTS "Users can update own profile" ON public.user_profiles;
DROP POLICY IF EXISTS "Users can insert own feedback" ON public.feedback_issues;
DROP POLICY IF EXISTS "Users can read own feedback" ON public.feedback_issues;

CREATE POLICY "select_own_watchlists" ON public.watchlists
    FOR SELECT TO authenticated USING (auth.uid() = user_id);
CREATE POLICY "insert_own_watchlists" ON public.watchlists
    FOR INSERT TO authenticated WITH CHECK (auth.uid() = user_id);
CREATE POLICY "update_own_watchlists" ON public.watchlists
    FOR UPDATE TO authenticated USING (auth.uid() = user_id) WITH CHECK (auth.uid() = user_id);
CREATE POLICY "delete_own_watchlists" ON public.watchlists
    FOR DELETE TO authenticated USING (auth.uid() = user_id);

CREATE POLICY "select_own_search_history" ON public.search_history
    FOR SELECT TO authenticated USING (auth.uid() = user_id);
CREATE POLICY "insert_own_search_history" ON public.search_history
    FOR INSERT TO authenticated WITH CHECK (auth.uid() = user_id);
CREATE POLICY "delete_own_search_history" ON public.search_history
    FOR DELETE TO authenticated USING (auth.uid() = user_id);

CREATE POLICY "select_own_predictions" ON public.predictions
    FOR SELECT TO authenticated USING (auth.uid() = user_id);
CREATE POLICY "insert_own_predictions" ON public.predictions
    FOR INSERT TO authenticated WITH CHECK (auth.uid() = user_id);

CREATE POLICY "select_saved_models" ON public.saved_models
    FOR SELECT TO authenticated USING (true);

CREATE POLICY "Users can read own profile" ON public.user_profiles
    FOR SELECT TO authenticated USING (auth.uid() = id);
CREATE POLICY "Users can update own profile" ON public.user_profiles
    FOR UPDATE TO authenticated USING (auth.uid() = id) WITH CHECK (auth.uid() = id);

CREATE POLICY "Users can insert own feedback" ON public.feedback_issues
    FOR INSERT TO authenticated WITH CHECK (auth.uid() = user_id);
CREATE POLICY "Users can read own feedback" ON public.feedback_issues
    FOR SELECT TO authenticated USING (auth.uid() = user_id);

CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO public.user_profiles (
        id,
        email,
        full_name,
        avatar_url,
        provider,
        first_seen_at,
        last_seen_at,
        created_at,
        updated_at
    )
    VALUES (
        NEW.id,
        NEW.email,
        COALESCE(
            NEW.raw_user_meta_data->>'full_name',
            NEW.raw_user_meta_data->>'name',
            split_part(NEW.email, '@', 1)
        ),
        COALESCE(NEW.raw_user_meta_data->>'avatar_url', NEW.raw_user_meta_data->>'picture', ''),
        COALESCE(NEW.raw_app_meta_data->>'provider', 'google'),
        COALESCE(NEW.created_at, now()),
        now(),
        COALESCE(NEW.created_at, now()),
        now()
    )
    ON CONFLICT (id) DO UPDATE
    SET
        email = EXCLUDED.email,
        full_name = EXCLUDED.full_name,
        avatar_url = EXCLUDED.avatar_url,
        provider = EXCLUDED.provider,
        last_seen_at = now(),
        updated_at = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
CREATE TRIGGER on_auth_user_created
    AFTER INSERT OR UPDATE ON auth.users
    FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();

CREATE OR REPLACE FUNCTION public.handle_update_user_profiles()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS on_user_profile_updated ON public.user_profiles;
CREATE TRIGGER on_user_profile_updated
    BEFORE UPDATE ON public.user_profiles
    FOR EACH ROW EXECUTE FUNCTION public.handle_update_user_profiles();

CREATE OR REPLACE FUNCTION public.handle_update_feedback_issues()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS on_feedback_issue_updated ON public.feedback_issues;
CREATE TRIGGER on_feedback_issue_updated
    BEFORE UPDATE ON public.feedback_issues
    FOR EACH ROW EXECUTE FUNCTION public.handle_update_feedback_issues();

INSERT INTO public.user_profiles (
    id,
    email,
    full_name,
    avatar_url,
    provider,
    first_seen_at,
    last_seen_at,
    created_at,
    updated_at
)
SELECT
    u.id,
    u.email,
    COALESCE(
        u.raw_user_meta_data->>'full_name',
        u.raw_user_meta_data->>'name',
        split_part(u.email, '@', 1)
    ) AS full_name,
    COALESCE(u.raw_user_meta_data->>'avatar_url', u.raw_user_meta_data->>'picture', '') AS avatar_url,
    COALESCE(u.raw_app_meta_data->>'provider', 'google') AS provider,
    COALESCE(u.created_at, now()) AS first_seen_at,
    now() AS last_seen_at,
    COALESCE(u.created_at, now()) AS created_at,
    now() AS updated_at
FROM auth.users u
ON CONFLICT (id) DO UPDATE
SET
    email = EXCLUDED.email,
    full_name = COALESCE(NULLIF(EXCLUDED.full_name, ''), public.user_profiles.full_name),
    avatar_url = COALESCE(NULLIF(EXCLUDED.avatar_url, ''), public.user_profiles.avatar_url),
    provider = COALESCE(NULLIF(EXCLUDED.provider, ''), public.user_profiles.provider, 'google'),
    first_seen_at = COALESCE(public.user_profiles.first_seen_at, EXCLUDED.first_seen_at),
    last_seen_at = GREATEST(public.user_profiles.last_seen_at, EXCLUDED.last_seen_at),
    updated_at = now();

UPDATE public.feedback_issues f
SET
    user_id = p.id,
    updated_at = now()
FROM public.user_profiles p
WHERE f.user_id IS NULL
  AND f.email IS NOT NULL
  AND lower(f.email) = lower(p.email);
