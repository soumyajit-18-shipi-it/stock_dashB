import { LogOut, ShieldAlert, User as UserIcon, ChevronDown } from 'lucide-react';
import { useState, useRef, useEffect } from 'react';

import { useAuth } from '../hooks/useAuth';
import { useUIStore } from '../store/ui_store';

export function UserMenu() {
  const { user, logout, isAdmin } = useAuth();
  const { setCurrentRoute } = useUIStore();
  const [isOpen, setIsOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    }
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  if (!user) return null;

  const metadata = user.user_metadata || {};
  const name = metadata.full_name || metadata.name || user.email?.split('@')[0] || 'User';
  const email = user.email || '';
  const avatarUrl = metadata.avatar_url || metadata.picture;

  return (
    <div className="relative" ref={dropdownRef}>
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center gap-2 p-1.5 rounded-lg bg-slate-800 border border-slate-700 hover:bg-slate-700 transition-colors"
        aria-expanded={isOpen}
        aria-haspopup="true"
      >
        {avatarUrl ? (
          <img
            src={avatarUrl}
            alt={name}
            className="h-6 w-6 rounded-full object-cover border border-slate-600"
            referrerPolicy="no-referrer"
          />
        ) : (
          <div className="h-6 w-6 rounded-full bg-emerald-500 flex items-center justify-center text-xs font-bold text-white uppercase">
            {name.charAt(0)}
          </div>
        )}
        <span className="hidden md:inline text-xs font-medium text-slate-200 truncate max-w-[100px]">
          {name}
        </span>
        <ChevronDown className="h-3 w-3 text-slate-400" />
      </button>

      {isOpen && (
        <div className="absolute right-0 mt-2 w-56 rounded-lg border border-slate-800 bg-slate-900 shadow-xl z-50 py-1">
          <div className="px-4 py-2.5 border-b border-slate-800">
            <p className="text-sm font-semibold text-white truncate">{name}</p>
            <p className="text-xs text-slate-400 truncate">{email}</p>
            {isAdmin && (
              <span className="mt-1 inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-bold bg-emerald-400/20 text-emerald-400">
                Admin
              </span>
            )}
          </div>

          <div className="py-1">
            {isAdmin && (
              <button
                onClick={() => {
                  setIsOpen(false);
                  setCurrentRoute('/admin/stats');
                }}
                className="flex w-full items-center gap-2 px-4 py-2 text-sm text-slate-300 hover:bg-slate-800 hover:text-white transition-colors"
              >
                <ShieldAlert className="h-4 w-4 text-emerald-400" />
                Admin Stats
              </button>
            )}

            <button
              onClick={() => {
                setIsOpen(false);
                setCurrentRoute('/');
              }}
              className="flex w-full items-center gap-2 px-4 py-2 text-sm text-slate-300 hover:bg-slate-800 hover:text-white transition-colors"
            >
              <UserIcon className="h-4 w-4" />
              View Dashboard
            </button>

            <button
              onClick={async () => {
                setIsOpen(false);
                await logout();
                setCurrentRoute('/');
              }}
              className="flex w-full items-center gap-2 px-4 py-2 text-sm text-red-400 hover:bg-red-500/10 transition-colors"
            >
              <LogOut className="h-4 w-4" />
              Sign Out
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
export default UserMenu;
