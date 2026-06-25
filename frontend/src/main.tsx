import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';

import App from './App.tsx';
import './i18n';
import './index.css';
import { registerServiceWorker } from './pwa';
import { applyTheme, readInitialTheme } from './theme';

applyTheme(readInitialTheme());
registerServiceWorker();

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <App />
  </StrictMode>
);
