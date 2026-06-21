import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';

import App from './App.tsx';
import './i18n';
import './index.css';
import { applyTheme, readInitialTheme } from './theme';

applyTheme(readInitialTheme());

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <App />
  </StrictMode>
);
