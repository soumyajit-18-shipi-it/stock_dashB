import { create } from 'zustand';

import { supabase, isSupabaseConfigured } from '../lib/supabase';

import type { User } from '@supabase/supabase-js';

const VITE_API_URL = import.meta.env.VITE_API_URL;
const hasExplicitApiUrl = Boolean(VITE_API_URL && VITE_API_URL !== '/api/v1');
const FASTAPI_URL =
  hasExplicitApiUrl
    ? VITE_API_URL
    : typeof window !== 'undefined' &&
      (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1')
    ? 'http://localhost:8000/api/v1'
    : '/api/v1';

export interface AuthState {
  user: User | null;
  token: string | null;
  loading: boolean;
  error: string | null;
  isAdmin: boolean;
  login: () => Promise<void>;
  logout: () => Promise<void>;
  initialize: () => () => void;
}

const adminEmails = (import.meta.env.VITE_ADMIN_EMAILS || '')
  .split(',')
  .map((email: string) => email.trim().toLowerCase());

function checkIsAdmin(email?: string) {
  if (!email) return false;
  return adminEmails.includes(email.toLowerCase());
}

async function syncProfile(accessToken: string) {
  try {
    await fetch(`${FASTAPI_URL}/auth/sync-profile`, {
      method: 'POST',
      headers: {
        Authorization: `Bearer ${accessToken}`,
        'Content-Type': 'application/json',
      },
    });
  } catch (err) {
    console.warn('Profile sync failed; dashboard data may update after the next authenticated API call.', err);
  }
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  token: null,
  loading: true,
  error: null,
  isAdmin: false,

  login: async () => {
    set({ loading: true, error: null });
    if (!isSupabaseConfigured) {
      set({
        error: 'Supabase auth is not configured. Please set VITE_SUPABASE_URL and VITE_SUPABASE_ANON_KEY.',
        loading: false,
      });
      return;
    }
    try {
      const redirectTo = `${window.location.origin}/auth/callback`;
      const { error } = await supabase.auth.signInWithOAuth({
        provider: 'google',
        options: {
          redirectTo,
        },
      });
      if (error) throw error;
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : String(err);
      set({ error: msg, loading: false });
    }
  },

  logout: async () => {
    if (!isSupabaseConfigured) {
      set({ user: null, token: null, isAdmin: false, loading: false });
      return;
    }
    set({ loading: true, error: null });
    try {
      const { error } = await supabase.auth.signOut();
      if (error) throw error;
      set({ user: null, token: null, isAdmin: false, loading: false });
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : String(err);
      set({ error: msg, loading: false });
    }
  },

  initialize: () => {
    if (!isSupabaseConfigured) {
      set({ loading: false });
      return () => {};
    }
    
    // Get initial session
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    supabase.auth.getSession().then(({ data: { session } }: { data: { session: any } }) => {
      if (session) {
        void syncProfile(session.access_token);
        set({
          user: session.user,
          token: session.access_token,
          isAdmin: checkIsAdmin(session.user.email),
          loading: false,
        });
      } else {
        set({ loading: false });
      }
    });

    // Listen for auth changes
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const { data: { subscription } } = supabase.auth.onAuthStateChange((_event: string, session: any) => {
      if (session) {
        void syncProfile(session.access_token);
        set({
          user: session.user,
          token: session.access_token,
          isAdmin: checkIsAdmin(session.user.email),
          loading: false,
        });
      } else {
        set({ user: null, token: null, isAdmin: false, loading: false });
      }
    });

    return () => {
      subscription.unsubscribe();
    };
  },
}));
