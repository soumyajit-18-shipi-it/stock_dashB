import { createClient } from '@supabase/supabase-js';

import type { Database } from '../types/supabase';

const supabaseUrl = import.meta.env.VITE_SUPABASE_URL || '';
const supabasePublishableKey = import.meta.env.VITE_SUPABASE_PUBLISHABLE_KEY || '';
const supabaseAnonKey = import.meta.env.VITE_SUPABASE_ANON_KEY || '';
const supabaseClientKey = supabasePublishableKey || supabaseAnonKey;

export const isSupabaseConfigured = Boolean(
  supabaseUrl &&
  supabaseClientKey &&
  !supabaseUrl.includes('your-project') &&
  !supabaseClientKey.includes('your-supabase') &&
  !supabaseClientKey.includes('your_publishable') &&
  supabaseUrl !== '' &&
  supabaseClientKey !== ''
);

export const supabase = isSupabaseConfigured
  ? createClient<Database>(supabaseUrl, supabaseClientKey)
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  : (null as any);
