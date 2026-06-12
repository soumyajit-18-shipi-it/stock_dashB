import { useEffect } from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { AISettingsModal, Navbar } from './components';
import { Dashboard } from './pages';
import i18n from './i18n';
import { useUIStore } from './store/ui_store';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
    },
  },
});

function App() {
  const { darkMode, language, toggleDarkMode } = useUIStore();

  useEffect(() => {
    void i18n.changeLanguage(language);
  }, [language]);

  return (
    <QueryClientProvider client={queryClient}>
      <div className={`min-h-screen ${darkMode ? 'dark' : ''} bg-white dark:bg-slate-900`}>
        <Navbar darkMode={darkMode} toggleDarkMode={toggleDarkMode} />
        <Dashboard />
        <AISettingsModal />
      </div>
    </QueryClientProvider>
  );
}
export default App;
