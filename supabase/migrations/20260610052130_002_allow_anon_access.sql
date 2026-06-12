-- Drop existing RLS policies that require authentication
DROP POLICY IF EXISTS "select_own_watchlists" ON watchlists;
DROP POLICY IF EXISTS "insert_own_watchlists" ON watchlists;
DROP POLICY IF EXISTS "update_own_watchlists" ON watchlists;
DROP POLICY IF EXISTS "delete_own_watchlists" ON watchlists;
DROP POLICY IF EXISTS "select_own_search_history" ON search_history;
DROP POLICY IF EXISTS "insert_own_search_history" ON search_history;
DROP POLICY IF EXISTS "delete_own_search_history" ON search_history;
DROP POLICY IF EXISTS "select_own_users" ON users;
DROP POLICY IF EXISTS "insert_own_users" ON users;
DROP POLICY IF EXISTS "update_own_users" ON users;
DROP POLICY IF EXISTS "select_predictions" ON predictions;
DROP POLICY IF EXISTS "insert_predictions" ON predictions;
DROP POLICY IF EXISTS "select_saved_models" ON saved_models;

-- Create new policies allowing anon access for demo
CREATE POLICY "allow_all_watchlists" ON watchlists FOR ALL
    TO anon USING (true) WITH CHECK (true);
CREATE POLICY "allow_all_search_history" ON search_history FOR ALL
    TO anon USING (true) WITH CHECK (true);
CREATE POLICY "allow_all_predictions" ON predictions FOR ALL
    TO anon USING (true) WITH CHECK (true);
CREATE POLICY "allow_all_saved_models" ON saved_models FOR ALL
    TO anon USING (true) WITH CHECK (true);
CREATE POLICY "allow_all_users" ON users FOR ALL
    TO anon USING (true) WITH CHECK (true);

-- Also allow authenticated users
CREATE POLICY "auth_watchlists" ON watchlists FOR ALL
    TO authenticated USING (true) WITH CHECK (true);
CREATE POLICY "auth_search_history" ON search_history FOR ALL
    TO authenticated USING (true) WITH CHECK (true);
CREATE POLICY "auth_predictions" ON predictions FOR ALL
    TO authenticated USING (true) WITH CHECK (true);
CREATE POLICY "auth_saved_models" ON saved_models FOR ALL
    TO authenticated USING (true) WITH CHECK (true);
CREATE POLICY "auth_users" ON users FOR ALL
    TO authenticated USING (true) WITH CHECK (true);
