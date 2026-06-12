export type ThemeName = 'light' | 'dark';

export function readInitialTheme(): ThemeName {
  return localStorage.getItem('theme') === 'light' ? 'light' : 'dark';
}

export function applyTheme(theme: ThemeName) {
  const root = document.documentElement;
  root.classList.toggle('dark', theme === 'dark');
  root.dataset.theme = theme;
  root.style.colorScheme = theme;
  root.style.setProperty('--app-bg', theme === 'dark' ? '#0f172a' : '#f8fafc');
  root.style.setProperty('--app-surface', theme === 'dark' ? '#1e293b' : '#ffffff');
  root.style.setProperty('--app-surface-muted', theme === 'dark' ? '#334155' : '#f1f5f9');
  root.style.setProperty('--app-border', theme === 'dark' ? '#334155' : '#cbd5e1');
  root.style.setProperty('--app-text', theme === 'dark' ? '#f8fafc' : '#0f172a');
  root.style.setProperty('--app-muted', theme === 'dark' ? '#94a3b8' : '#475569');
  root.style.setProperty('--chart-paper-bg', theme === 'dark' ? 'transparent' : '#ffffff');
  root.style.setProperty('--chart-plot-bg', theme === 'dark' ? 'transparent' : '#ffffff');
  root.style.setProperty('--chart-font', theme === 'dark' ? '#94a3b8' : '#475569');
  root.style.setProperty('--chart-title', theme === 'dark' ? '#f1f5f9' : '#0f172a');
  root.style.setProperty('--chart-grid', theme === 'dark' ? '#334155' : '#e2e8f0');
  root.style.setProperty('--chart-line', theme === 'dark' ? '#475569' : '#cbd5e1');
}
