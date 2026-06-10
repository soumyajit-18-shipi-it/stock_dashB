import { useState, useEffect } from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Navbar } from './components';
import { Dashboard } from './pages';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
    },
  },
});

function App() {
  const [darkMode, setDarkMode] = useState(() => {
    // Initialise from localStorage if present
    const stored = localStorage.getItem('theme');
    return stored === 'dark';
  });

  // Persist changes to localStorage
  useEffect(() => {
    localStorage.setItem('theme', darkMode ? 'dark' : 'light');
  }, [darkMode]);

  const toggleDarkMode = () => setDarkMode(!darkMode);

  return (
    <QueryClientProvider client={queryClient}>
      <div className={`min-h-screen ${darkMode ? 'dark' : ''} bg-white dark:bg-slate-900`}>
        <Navbar darkMode={darkMode} toggleDarkMode={toggleDarkMode} />
        <Dashboard />
      </div>
    </QueryClientProvider>
  );
}
export default App;
