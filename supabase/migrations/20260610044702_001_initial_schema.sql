-- Users table (extends Supabase auth.users)
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email TEXT UNIQUE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Watchlists table
CREATE TABLE IF NOT EXISTS watchlists (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    ticker TEXT NOT NULL,
    name TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Search history table
CREATE TABLE IF NOT EXISTS search_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    ticker TEXT NOT NULL,
    searched_at TIMESTAMPTZ DEFAULT NOW()
);

-- Predictions table
CREATE TABLE IF NOT EXISTS predictions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    ticker TEXT NOT NULL,
    model TEXT NOT NULL,
    predicted_price DECIMAL(18, 4),
    actual_price DECIMAL(18, 4),
    confidence DECIMAL(5, 4),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Saved models metadata table
CREATE TABLE IF NOT EXISTS saved_models (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    model_name TEXT UNIQUE NOT NULL,
    file_path TEXT NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Enable RLS on all tables
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE watchlists ENABLE ROW LEVEL SECURITY;
ALTER TABLE search_history ENABLE ROW LEVEL SECURITY;
ALTER TABLE predictions ENABLE ROW LEVEL SECURITY;
ALTER TABLE saved_models ENABLE ROW LEVEL SECURITY;

-- RLS policies for users
CREATE POLICY "select_own_users" ON users FOR SELECT
    TO authenticated USING (auth.uid()::text = id::text);
CREATE POLICY "insert_own_users" ON users FOR INSERT
    TO authenticated WITH CHECK (auth.uid()::text = id::text);
CREATE POLICY "update_own_users" ON users FOR UPDATE
    TO authenticated USING (auth.uid()::text = id::text) WITH CHECK (auth.uid()::text = id::text);

-- RLS policies for watchlists
CREATE POLICY "select_own_watchlists" ON watchlists FOR SELECT
    TO authenticated USING (auth.uid()::text = user_id::text);
CREATE POLICY "insert_own_watchlists" ON watchlists FOR INSERT
    TO authenticated WITH CHECK (auth.uid()::text = user_id::text);
CREATE POLICY "update_own_watchlists" ON watchlists FOR UPDATE
    TO authenticated USING (auth.uid()::text = user_id::text) WITH CHECK (auth.uid()::text = user_id::text);
CREATE POLICY "delete_own_watchlists" ON watchlists FOR DELETE
    TO authenticated USING (auth.uid()::text = user_id::text);

-- RLS policies for search_history
CREATE POLICY "select_own_search_history" ON search_history FOR SELECT
    TO authenticated USING (auth.uid()::text = user_id::text);
CREATE POLICY "insert_own_search_history" ON search_history FOR INSERT
    TO authenticated WITH CHECK (auth.uid()::text = user_id::text);
CREATE POLICY "delete_own_search_history" ON search_history FOR DELETE
    TO authenticated USING (auth.uid()::text = user_id::text);

-- RLS policies for predictions (public read, authenticated insert)
CREATE POLICY "select_predictions" ON predictions FOR SELECT
    TO authenticated USING (true);
CREATE POLICY "insert_predictions" ON predictions FOR INSERT
    TO authenticated WITH CHECK (true);

-- RLS policies for saved_models (public read for authenticated)
CREATE POLICY "select_saved_models" ON saved_models FOR SELECT
    TO authenticated USING (true);

-- Create indexes for performance
CREATE INDEX idx_watchlists_user_id ON watchlists(user_id);
CREATE INDEX idx_watchlists_ticker ON watchlists(ticker);
CREATE INDEX idx_search_history_user_id ON search_history(user_id);
CREATE INDEX idx_search_history_ticker ON search_history(ticker);
CREATE INDEX idx_predictions_ticker ON predictions(ticker);
CREATE INDEX idx_predictions_created_at ON predictions(created_at);
