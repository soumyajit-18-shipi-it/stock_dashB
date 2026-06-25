-- Enforce Supabase-auth scoped user data after Google login.

CREATE EXTENSION IF NOT EXISTS pgcrypto;

ALTER TABLE public.watchlists
    ADD COLUMN IF NOT EXISTS company_name TEXT;

ALTER TABLE public.search_history
    ADD COLUMN IF NOT EXISTS query TEXT;

ALTER TABLE public.predictions
    ADD COLUMN IF NOT EXISTS user_id UUID;

UPDATE public.watchlists
SET ticker = upper(ticker),
    company_name = COALESCE(company_name, name)
WHERE ticker IS NOT NULL;

UPDATE public.search_history
SET ticker = upper(ticker),
    query = COALESCE(query, ticker)
WHERE ticker IS NOT NULL;

DELETE FROM public.watchlists a
USING public.watchlists b
WHERE a.ctid < b.ctid
  AND a.user_id = b.user_id
  AND a.ticker = b.ticker;

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

ALTER TABLE public.watchlists ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.search_history ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.predictions ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "allow_all_watchlists" ON public.watchlists;
DROP POLICY IF EXISTS "allow_all_search_history" ON public.search_history;
DROP POLICY IF EXISTS "allow_all_predictions" ON public.predictions;
DROP POLICY IF EXISTS "auth_watchlists" ON public.watchlists;
DROP POLICY IF EXISTS "auth_search_history" ON public.search_history;
DROP POLICY IF EXISTS "auth_predictions" ON public.predictions;
DROP POLICY IF EXISTS "select_own_watchlists" ON public.watchlists;
DROP POLICY IF EXISTS "insert_own_watchlists" ON public.watchlists;
DROP POLICY IF EXISTS "update_own_watchlists" ON public.watchlists;
DROP POLICY IF EXISTS "delete_own_watchlists" ON public.watchlists;
DROP POLICY IF EXISTS "select_own_search_history" ON public.search_history;
DROP POLICY IF EXISTS "insert_own_search_history" ON public.search_history;
DROP POLICY IF EXISTS "delete_own_search_history" ON public.search_history;
DROP POLICY IF EXISTS "select_predictions" ON public.predictions;
DROP POLICY IF EXISTS "insert_predictions" ON public.predictions;

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

CREATE UNIQUE INDEX IF NOT EXISTS idx_watchlists_user_ticker_unique
    ON public.watchlists(user_id, ticker);
CREATE INDEX IF NOT EXISTS idx_search_history_user_created
    ON public.search_history(user_id, searched_at DESC);
CREATE INDEX IF NOT EXISTS idx_predictions_user_created
    ON public.predictions(user_id, created_at DESC);
