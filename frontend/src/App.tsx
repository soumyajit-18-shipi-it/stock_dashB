import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { useEffect, useState } from 'react';

import { AISettingsModal, Navbar, FeedbackWidget, LoginGate } from './components';
import { useAuth } from './hooks/useAuth';
import i18n from './i18n';
import { Dashboard, AuthCallback, AdminStats, PortfolioDashboard } from './pages';
import { useAuthStore } from './store/auth_store';
import { useUIStore } from './store/ui_store';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      staleTime: 5 * 60 * 1000,
      gcTime: 30 * 60 * 1000,
      retry: 2,
      retryDelay: (attempt) => Math.min(1000 * 2 ** attempt, 8000),
    },
  },
});

function App() {
  const { darkMode, language, lowDataMode, toggleDarkMode, currentRoute } = useUIStore();
  const initializeAuth = useAuthStore((state) => state.initialize);
  const { user, loading: authLoading } = useAuth();
  const [online, setOnline] = useState(navigator.onLine);

  useEffect(() => {
    const unsubscribe = initializeAuth();
    return () => unsubscribe();
  }, [initializeAuth]);

  useEffect(() => {
    void i18n.changeLanguage(language);
  }, [language]);

  useEffect(() => {
    const updateStatus = () => setOnline(navigator.onLine);
    window.addEventListener('online', updateStatus);
    window.addEventListener('offline', updateStatus);
    return () => {
      window.removeEventListener('online', updateStatus);
      window.removeEventListener('offline', updateStatus);
    };
  }, []);

  useEffect(() => {
    const handlePopState = () => {
      useUIStore.setState({ currentRoute: window.location.pathname });
    };
    window.addEventListener('popstate', handlePopState);
    return () => window.removeEventListener('popstate', handlePopState);
  }, []);

  if (currentRoute === '/auth/callback') {
    return (
      <QueryClientProvider client={queryClient}>
        <div className={`min-h-screen ${darkMode ? 'dark' : ''} bg-white dark:bg-slate-900`}>
          <AuthCallback />
        </div>
      </QueryClientProvider>
    );
  }

  if (authLoading) {
    return (
      <div className="min-h-screen bg-slate-950 flex items-center justify-center">
        <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-r-2 border-emerald-500 mx-auto"></div>
      </div>
    );
  }

  if (!user) {
    return (
      <QueryClientProvider client={queryClient}>
        <div className={`min-h-screen ${darkMode ? 'dark' : ''} bg-white dark:bg-slate-900`}>
          <LoginGate />
        </div>
      </QueryClientProvider>
    );
  }

  const renderRoute = () => {
    if (currentRoute === '/admin/stats') {
      return <AdminStats />;
    }
    if (currentRoute === '/portfolio') {
      return <PortfolioDashboard />;
    }
    return <Dashboard />;
  };

  return (
    <QueryClientProvider client={queryClient}>
      <div className={`min-h-screen ${darkMode ? 'dark' : ''} bg-white dark:bg-slate-900`}>
        <Navbar darkMode={darkMode} toggleDarkMode={toggleDarkMode} />
        {(!online || lowDataMode) && (
          <div className="border-b border-slate-700 bg-slate-950 px-4 py-2 text-center text-sm text-slate-200">
            {!online
              ? 'Offline mode: cached screens may be available; live market and AI data need a connection.'
              : 'Low-data mode is enabled: cached API responses are reused longer and heavy refreshes are reduced.'}
          </div>
        )}
        {renderRoute()}
        <AISettingsModal />
        <FeedbackWidget />
      </div>
    </QueryClientProvider>
  );
}
export default App;
