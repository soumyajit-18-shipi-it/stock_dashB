import { useEffect } from 'react';

import { supabase } from '../lib/supabase';
import { useUIStore } from '../store/ui_store';

export function AuthCallback() {
  const { setCurrentRoute } = useUIStore();

  useEffect(() => {
    supabase.auth.getSession().then(() => {
      setCurrentRoute('/');
    });
  }, [setCurrentRoute]);

  return (
    <div className="min-h-screen bg-slate-950 flex items-center justify-center">
      <div className="text-center space-y-4">
        <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-r-2 border-emerald-500 mx-auto"></div>
        <p className="text-slate-400 text-sm">Completing sign in, redirecting...</p>
      </div>
    </div>
  );
}
export default AuthCallback;
