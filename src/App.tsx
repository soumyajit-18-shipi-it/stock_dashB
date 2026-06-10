import { useState } from 'react';
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
  const [darkMode, setDarkMode] = useState(true);

  const toggleDarkMode = () => setDarkMode(!darkMode);

  return (
    <QueryClientProvider client={queryClient}>
      <div className={`min-h-screen ${darkMode ? 'dark' : ''}`}>
        <Navbar darkMode={darkMode} toggleDarkMode={toggleDarkMode} />
        <Dashboard />
      </div>
    </QueryClientProvider>
  );
}

export default App;
