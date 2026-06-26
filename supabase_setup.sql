-- ==========================================
-- STOCK INTELLIGENCE DASHBOARD SUPABASE SETUP
-- ==========================================
-- This file contains the complete consolidated database schema.
-- Run this script directly in the Supabase Web Dashboard SQL Editor.
-- Open your project -> SQL Editor -> New Query -> Paste this entire script -> Click Run.

-- ==========================================
-- PHASE 1: Initial Schema Setup
-- ==========================================

-- Users table (extends Supabase auth.users)
CREATE TABLE IF NOT EXISTS public.users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email TEXT UNIQUE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Watchlists table
CREATE TABLE IF NOT EXISTS public.watchlists (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    ticker TEXT NOT NULL,
    name TEXT,
    company_name TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Search history table
CREATE TABLE IF NOT EXISTS public.search_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    query TEXT,
    ticker TEXT NOT NULL,
    searched_at TIMESTAMPTZ DEFAULT NOW()
);

-- Predictions table
CREATE TABLE IF NOT EXISTS public.predictions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    ticker TEXT NOT NULL,
    model TEXT NOT NULL,
    predicted_price DECIMAL(18, 4),
    actual_price DECIMAL(18, 4),
    confidence DECIMAL(5, 4),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Saved models metadata table
CREATE TABLE IF NOT EXISTS public.saved_models (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    model_name TEXT UNIQUE NOT NULL,
    file_path TEXT NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Enable RLS on all tables
ALTER TABLE public.users ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.watchlists ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.search_history ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.predictions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.saved_models ENABLE ROW LEVEL SECURITY;

-- ==========================================
-- PHASE 2: Auth-Scoped Access Policies
-- ==========================================

-- Drop existing RLS policies if any to prevent duplicate errors
DROP POLICY IF EXISTS "select_own_users" ON public.users;
DROP POLICY IF EXISTS "insert_own_users" ON public.users;
DROP POLICY IF EXISTS "update_own_users" ON public.users;
DROP POLICY IF EXISTS "select_own_watchlists" ON public.watchlists;
DROP POLICY IF EXISTS "insert_own_watchlists" ON public.watchlists;
DROP POLICY IF EXISTS "update_own_watchlists" ON public.watchlists;
DROP POLICY IF EXISTS "delete_own_watchlists" ON public.watchlists;
DROP POLICY IF EXISTS "select_own_search_history" ON public.search_history;
DROP POLICY IF EXISTS "insert_own_search_history" ON public.search_history;
DROP POLICY IF EXISTS "delete_own_search_history" ON public.search_history;
DROP POLICY IF EXISTS "select_predictions" ON public.predictions;
DROP POLICY IF EXISTS "insert_predictions" ON public.predictions;
DROP POLICY IF EXISTS "select_saved_models" ON public.saved_models;

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

-- User-specific rows are available only to the authenticated owner.
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

-- Saved model metadata is public app metadata; writes stay backend-only.
CREATE POLICY "select_saved_models" ON public.saved_models
    FOR SELECT TO authenticated USING (true);

-- Create performance indexes
CREATE INDEX IF NOT EXISTS idx_watchlists_user_id ON public.watchlists(user_id);
CREATE INDEX IF NOT EXISTS idx_watchlists_ticker ON public.watchlists(ticker);
CREATE UNIQUE INDEX IF NOT EXISTS idx_watchlists_user_ticker_unique ON public.watchlists(user_id, ticker);
CREATE INDEX IF NOT EXISTS idx_search_history_user_id ON public.search_history(user_id);
CREATE INDEX IF NOT EXISTS idx_search_history_ticker ON public.search_history(ticker);
CREATE INDEX IF NOT EXISTS idx_search_history_user_created ON public.search_history(user_id, searched_at DESC);
CREATE INDEX IF NOT EXISTS idx_predictions_ticker ON public.predictions(ticker);
CREATE INDEX IF NOT EXISTS idx_predictions_user_created ON public.predictions(user_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_predictions_created_at ON public.predictions(created_at);

-- ==========================================
-- PHASE 3: Auth Synchronizer & Feedback System
-- ==========================================

-- Create user_profiles table (directly syncs with auth.users)
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

-- Indexes for user_profiles
CREATE INDEX IF NOT EXISTS idx_user_profiles_email ON public.user_profiles(email);
CREATE INDEX IF NOT EXISTS idx_user_profiles_created_at ON public.user_profiles(created_at);

-- Enable RLS on user_profiles
ALTER TABLE public.user_profiles ENABLE ROW LEVEL SECURITY;

-- Policies for user_profiles
DROP POLICY IF EXISTS "Users can read own profile" ON public.user_profiles;
DROP POLICY IF EXISTS "Users can update own profile" ON public.user_profiles;

-- Users can read only their own profile
CREATE POLICY "Users can read own profile" ON public.user_profiles
    FOR SELECT TO authenticated USING (auth.uid() = id);

-- Users can update only their own profile
CREATE POLICY "Users can update own profile" ON public.user_profiles
    FOR UPDATE TO authenticated USING (auth.uid() = id) WITH CHECK (auth.uid() = id);

-- Trigger function to automatically handle new auth.users row
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

-- Create the trigger on auth.users
DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
CREATE TRIGGER on_auth_user_created
    AFTER INSERT OR UPDATE ON auth.users
    FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();

-- Backfill existing Supabase Auth users into public.user_profiles.
-- Safe to paste and run from the Supabase Web Dashboard SQL Editor.
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

-- Trigger for updating updated_at on user_profiles
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

-- Create feedback_issues table
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

-- Indexes for feedback_issues
CREATE INDEX IF NOT EXISTS idx_feedback_user_id ON public.feedback_issues(user_id);
CREATE INDEX IF NOT EXISTS idx_feedback_email ON public.feedback_issues(email);
CREATE INDEX IF NOT EXISTS idx_feedback_category ON public.feedback_issues(category);
CREATE INDEX IF NOT EXISTS idx_feedback_status ON public.feedback_issues(status);
CREATE INDEX IF NOT EXISTS idx_feedback_created_at ON public.feedback_issues(created_at);

-- Enable RLS on feedback_issues
ALTER TABLE public.feedback_issues ENABLE ROW LEVEL SECURITY;

-- Policies for feedback_issues
DROP POLICY IF EXISTS "Users can insert own feedback" ON public.feedback_issues;
DROP POLICY IF EXISTS "Users can read own feedback" ON public.feedback_issues;

-- Logged-in users can insert their own feedback
CREATE POLICY "Users can insert own feedback" ON public.feedback_issues
    FOR INSERT TO authenticated WITH CHECK (auth.uid() = user_id);

-- Logged-in users can read their own feedback
CREATE POLICY "Users can read own feedback" ON public.feedback_issues
    FOR SELECT TO authenticated USING (auth.uid() = user_id);

-- Trigger for updating updated_at on feedback_issues
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

-- Backfill feedback rows created before user_id was recorded.
-- Server-side admin endpoints also match by email as a fallback.
UPDATE public.feedback_issues f
SET
    user_id = p.id,
    updated_at = now()
FROM public.user_profiles p
WHERE f.user_id IS NULL
  AND f.email IS NOT NULL
  AND lower(f.email) = lower(p.email);
