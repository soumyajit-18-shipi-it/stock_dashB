-- Create user_profiles table
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
-- Users can read only their own profile
CREATE POLICY "Users can read own profile" ON public.user_profiles
    FOR SELECT TO authenticated USING (auth.uid() = id);

-- Users can update only their own profile
CREATE POLICY "Users can update own profile" ON public.user_profiles
    FOR UPDATE TO authenticated USING (auth.uid() = id) WITH CHECK (auth.uid() = id);

-- Trigger function to handle new auth.users row
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO public.user_profiles (id, email, full_name, avatar_url, provider)
    VALUES (
        NEW.id,
        NEW.email,
        COALESCE(NEW.raw_user_meta_data->>'full_name', NEW.raw_user_meta_data->>'name', ''),
        COALESCE(NEW.raw_user_meta_data->>'avatar_url', NEW.raw_user_meta_data->>'picture', ''),
        COALESCE(NEW.app_metadata->>'provider', 'google')
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

-- Create the trigger on auth.users if it does not exist
DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
CREATE TRIGGER on_auth_user_created
    AFTER INSERT ON auth.users
    FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();

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
CREATE INDEX IF NOT EXISTS idx_feedback_category ON public.feedback_issues(category);
CREATE INDEX IF NOT EXISTS idx_feedback_status ON public.feedback_issues(status);
CREATE INDEX IF NOT EXISTS idx_feedback_created_at ON public.feedback_issues(created_at);

-- Enable RLS on feedback_issues
ALTER TABLE public.feedback_issues ENABLE ROW LEVEL SECURITY;

-- Policies for feedback_issues
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
