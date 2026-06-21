import { BarChart3, Moon, Settings, Sun } from 'lucide-react';
import { useTranslation } from 'react-i18next';

import { languages, type AppLanguage } from '../i18n';
import { WatchlistDropdown } from './WatchlistDropdown';
import { useUIStore } from '../store/ui_store';

interface NavbarProps {
  darkMode: boolean;
  toggleDarkMode: () => void;
}

export function Navbar({ darkMode, toggleDarkMode }: NavbarProps) {
  const { t } = useTranslation();
  const { language, setLanguage, setAiSettingsOpen } = useUIStore();

  return (
    <nav className="bg-slate-900/80 backdrop-blur-xl border-b border-slate-800 sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          <div className="flex items-center gap-3">
            <div className="bg-gradient-to-br from-emerald-400 to-emerald-600 p-2 rounded-xl">
              <BarChart3 className="h-6 w-6 text-white" />
            </div>
            <div>
              <h1 className="text-xl font-bold text-white">{t('appTitle')}</h1>
              <p className="text-xs text-slate-400">{t('appSubtitle')}</p>
            </div>
          </div>

          <div className="flex items-center gap-2">
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
          </div>
        </div>
      </div>
    </nav>
  );
}
