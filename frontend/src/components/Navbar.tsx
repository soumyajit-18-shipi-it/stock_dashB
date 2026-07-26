import {
  BarChart3,
  Bot,
  Briefcase,
  LayoutDashboard,
  Moon,
  Settings,
  Sun,
} from 'lucide-react';
import { useTranslation } from 'react-i18next';

import { languages, type AppLanguage } from '../i18n';
import { AuthButton } from './AuthButton';
import { UserMenu } from './UserMenu';
import { WatchlistDropdown } from './WatchlistDropdown';
import { useAuth } from '../hooks/useAuth';
import { useUIStore } from '../store/ui_store';

interface NavbarProps {
  darkMode: boolean;
  toggleDarkMode: () => void;
}

export function Navbar({ darkMode, toggleDarkMode }: NavbarProps) {
  const { t } = useTranslation();
  const {
    language,
    lowDataMode,
    currentRoute,
    setLanguage,
    setLowDataMode,
    setAiSettingsOpen,
    setAiChatOpen,
    setCurrentRoute,
  } = useUIStore();
  const { user } = useAuth();

  return (
    <nav className="bg-slate-900/80 backdrop-blur-xl border-b border-slate-800 sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          <div className="flex min-w-0 items-center gap-3">
            <div className="rounded-md bg-emerald-600 p-2">
              <BarChart3 className="h-6 w-6 text-white" />
            </div>
            <div className="hidden min-w-0 lg:block">
              <h1 className="text-xl font-bold text-white">{t('appTitle')}</h1>
              <p className="text-xs text-slate-400">{t('appSubtitle')}</p>
            </div>
            <div className="ml-2 hidden items-center gap-1 md:flex">
              <button
                type="button"
                onClick={() => setCurrentRoute('/')}
                className={`flex items-center gap-2 rounded-md px-3 py-2 text-sm ${
                  currentRoute === '/'
                    ? 'bg-slate-700 text-cyan-300'
                    : 'text-slate-300 hover:bg-slate-800'
                }`}
              >
                <LayoutDashboard className="h-4 w-4" />
                Stocks
              </button>
              <button
                type="button"
                onClick={() => setCurrentRoute('/portfolio')}
                className={`flex items-center gap-2 rounded-md px-3 py-2 text-sm ${
                  currentRoute === '/portfolio'
                    ? 'bg-slate-700 text-cyan-300'
                    : 'text-slate-300 hover:bg-slate-800'
                }`}
              >
                <Briefcase className="h-4 w-4" />
                Portfolio
              </button>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <div className="flex items-center gap-1 md:hidden">
              <button
                type="button"
                title="Stocks"
                onClick={() => setCurrentRoute('/')}
                className={`rounded-md p-2 ${
                  currentRoute === '/' ? 'bg-slate-700 text-cyan-300' : 'text-slate-400'
                }`}
              >
                <LayoutDashboard className="h-5 w-5" />
              </button>
              <button
                type="button"
                title="Portfolio"
                onClick={() => setCurrentRoute('/portfolio')}
                className={`rounded-md p-2 ${
                  currentRoute === '/portfolio'
                    ? 'bg-slate-700 text-cyan-300'
                    : 'text-slate-400'
                }`}
              >
                <Briefcase className="h-5 w-5" />
              </button>
            </div>
            <WatchlistDropdown />
            <a
              href="https://finance.yahoo.com/"
              target="_blank"
              rel="noopener noreferrer"
              className="hidden rounded-lg bg-slate-700 px-3 py-1.5 text-sm text-white transition-colors hover:bg-slate-600 sm:inline-flex"
            >
              {t('browseMoreTickers')}
            </a>
            <label htmlFor="language-select" className="sr-only">
              {t('language')}
            </label>
            <select
              id="language-select"
              value={language}
              onChange={(e) => setLanguage(e.target.value as AppLanguage)}
              className="max-w-28 rounded-lg border border-slate-700 bg-slate-800 px-2 py-1.5 text-sm text-white"
            >
              {languages.map((item) => (
                <option key={item.code} value={item.code}>
                  {item.label}
                </option>
              ))}
            </select>
            {user && (
              <button
                onClick={() => setAiChatOpen(true)}
                className="flex items-center gap-1.5 px-3 py-1.5 bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg text-sm font-semibold transition-all hover:scale-105 active:scale-95 shadow"
                aria-label={t('askAi')}
              >
                <Bot className="h-4 w-4" />
                <span>{t('askAi')}</span>
              </button>
            )}
            <button
              onClick={() => setAiSettingsOpen(true)}
              className="p-2 hover:bg-slate-800 rounded-lg transition-colors"
              aria-label={t('settings')}
            >
              <Settings className="h-5 w-5 text-slate-400" />
            </button>
            <button
              onClick={toggleDarkMode}
              className="p-2 hover:bg-slate-800 rounded-lg transition-colors"
              aria-label={t('toggleTheme')}
            >
              {darkMode ? (
                <Sun className="h-5 w-5 text-yellow-400" />
              ) : (
                <Moon className="h-5 w-5 text-slate-400" />
              )}
            </button>
            <button
              onClick={() => setLowDataMode(!lowDataMode)}
              className={`hidden rounded-lg px-3 py-1.5 text-sm transition-colors sm:inline-flex ${
                lowDataMode
                  ? 'bg-emerald-600 text-white hover:bg-emerald-700'
                  : 'bg-slate-700 text-white hover:bg-slate-600'
              }`}
              aria-pressed={lowDataMode}
            >
              Low data
            </button>
            {user ? <UserMenu /> : <AuthButton />}
          </div>
        </div>
      </div>
    </nav>
  );
}
