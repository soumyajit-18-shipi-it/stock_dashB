import { BarChart3, Shield, Star, MessageSquare, AlertTriangle } from 'lucide-react';

import { useAuth } from '../hooks/useAuth';
import { isSupabaseConfigured } from '../lib/supabase';

export function LoginGate() {
  const { login, loading, error } = useAuth();

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-md">
      {/* Background Decorative Blurs */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute -top-[40%] -left-[20%] w-[80%] h-[80%] rounded-full bg-emerald-500/10 blur-[120px]" />
        <div className="absolute -bottom-[40%] -right-[20%] w-[80%] h-[80%] rounded-full bg-emerald-600/10 blur-[120px]" />
      </div>

      <div className="relative w-full max-w-md bg-slate-900/90 border border-slate-800 rounded-3xl shadow-2xl p-8 overflow-hidden">
        {/* Upper Accent Line */}
        <div className="absolute top-0 inset-x-0 h-1 bg-gradient-to-r from-emerald-500 via-teal-500 to-emerald-600" />

        <div className="flex flex-col items-center text-center space-y-6">
          {/* Logo */}
          <div className="bg-gradient-to-br from-emerald-400 to-emerald-600 p-3 rounded-2xl shadow-lg shadow-emerald-500/10">
            <BarChart3 className="h-8 w-8 text-white animate-pulse" />
          </div>

          {/* Heading */}
          <div className="space-y-1">
            <h2 className="text-2xl font-bold text-white tracking-tight">
              Stock Intelligence Dashboard
            </h2>
            <p className="text-sm text-slate-400">
              Advanced stock analysis and predictive model tracking.
            </p>
          </div>

          {/* Bullet Points */}
          <div className="w-full text-left bg-slate-950/50 border border-slate-800/80 rounded-2xl p-5 space-y-3.5">
            <div className="flex items-start gap-3">
              <Star className="h-5 w-5 text-emerald-400 shrink-0 mt-0.5" />
              <div>
                <h4 className="text-xs font-semibold text-slate-200">Personalized Watchlist</h4>
                <p className="text-[11px] text-slate-400">Track and manage your favorite equities in one central hub.</p>
              </div>
            </div>

            <div className="flex items-start gap-3">
              <MessageSquare className="h-5 w-5 text-emerald-400 shrink-0 mt-0.5" />
              <div>
                <h4 className="text-xs font-semibold text-slate-200">Feedback Tracking</h4>
                <p className="text-[11px] text-slate-400">Directly submit bug reports or requests to development teams.</p>
              </div>
            </div>

            <div className="flex items-start gap-3">
              <Shield className="h-5 w-5 text-emerald-400 shrink-0 mt-0.5" />
              <div>
                <h4 className="text-xs font-semibold text-slate-200">Admin User Analytics</h4>
                <p className="text-[11px] text-slate-400">Allow authorized emails to view real-time counts and metrics.</p>
              </div>
            </div>
          </div>

          {/* Setup Warning if Supabase is unconfigured */}
          {!isSupabaseConfigured ? (
            <div className="w-full flex items-start gap-2.5 p-3 rounded-xl bg-red-500/10 border border-red-500/20 text-red-200 text-left text-xs leading-relaxed">
              <AlertTriangle className="h-5 w-5 text-red-400 shrink-0" />
              <span>
                <strong>Configuration Required:</strong> Supabase auth is not configured. Please set <code>VITE_SUPABASE_URL</code> and <code>VITE_SUPABASE_ANON_KEY</code> in your environment file.
              </span>
            </div>
          ) : (
            error && (
              <div className="w-full flex items-start gap-2.5 p-3 rounded-xl bg-red-500/10 border border-red-500/20 text-red-200 text-left text-xs">
                <AlertTriangle className="h-4 w-4 text-red-400 shrink-0 mt-0.5" />
                <span>{error}</span>
              </div>
            )
          )}

          {/* Actions */}
          <div className="w-full space-y-3.5">
            <button
              onClick={login}
              disabled={loading || !isSupabaseConfigured}
              className="w-full inline-flex items-center justify-center gap-2.5 px-4 py-3 bg-white hover:bg-slate-100 disabled:bg-slate-800 disabled:text-slate-500 disabled:opacity-50 text-slate-900 rounded-xl font-semibold shadow-lg transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-emerald-500 active:scale-[0.98]"
            >
              <svg className="h-4 w-4 shrink-0" viewBox="0 0 24 24" width="24" height="24" xmlns="http://www.w3.org/2000/svg">
                <g transform="matrix(1, 0, 0, 1, 0, 0)">
                  <path d="M21.35,11.1H12v2.7h5.38c-0.24,1.28 -0.96,2.37 -2.04,3.1v2.58h3.3c1.93,-1.78 3.04,-4.4 3.04,-7.48C21.68,11.83 21.56,11.4 21.35,11.1z" fill="#4285F4" />
                  <path d="M12,20.6c2.43,0 4.47,-0.8 5.96,-2.2l-3.3,-2.58c-0.92,0.62 -2.1,0.98 -3.3,0.98 -2.35,0 -4.34,-1.58 -5.05,-3.72H2.9v2.66C4.38,18.7 8.0,20.6 12,20.6z" fill="#34A853" />
                  <path d="M6.95,13.08c-0.18,-0.54 -0.28,-1.11 -0.28,-1.7s0.1,-1.16 0.28,-1.7V7.02H2.9C2.3,8.22 2,9.57 2,11s0.3,2.78 0.9,3.98l4.05,-2.9z" fill="#FBBC05" />
                  <path d="M12,5.62c1.32,0 2.5,0.45 3.44,1.35l2.58,-2.58C16.46,2.9 14.42,2.2 12,2.2c-4.0,0 -7.62,1.9 -9.1,4.82l4.05,2.9C7.66,7.2 9.65,5.62 12,5.62z" fill="#EA4335" />
                </g>
              </svg>
              {loading ? 'Redirecting to Google...' : 'Continue with Google'}
            </button>

            <p className="text-[10px] text-slate-500 leading-normal max-w-xs mx-auto">
              We use Google login only for authentication and user tracking.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
export default LoginGate;
