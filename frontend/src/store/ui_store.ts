import { create } from 'zustand';

import { isAppLanguage, readInitialLanguage, type AppLanguage } from '../i18n';
import { applyTheme, readInitialTheme, type ThemeName } from '../theme';

export type AiProvider = 'ollama' | 'openai' | 'gemini' | 'anthropic' | 'custom' | 'auto';

export interface AIProviderConfig {
  provider: AiProvider;
  apiKey?: string;
  baseUrl?: string;
  selectedModel?: string;
}

interface UIState {
  darkMode: boolean;
  language: AppLanguage;
  lowDataMode: boolean;
  aiChatOpen: boolean;
  aiSettingsOpen: boolean;
  aiProviderConfig: AIProviderConfig;
  currentRoute: string;
  setDarkMode: (darkMode: boolean) => void;
  toggleDarkMode: () => void;
  setLanguage: (language: AppLanguage) => void;
  setLowDataMode: (enabled: boolean) => void;
  setAiChatOpen: (open: boolean) => void;
  setAiSettingsOpen: (open: boolean) => void;
  setAiProviderConfig: (config: AIProviderConfig) => void;
  setCurrentRoute: (route: string) => void;
}

const defaultConfig: AIProviderConfig = {
  provider: 'auto',
  baseUrl: '',
};

function readConfig(): AIProviderConfig {
  try {
    const stored = localStorage.getItem('ai_provider_config');
    if (!stored) return defaultConfig;
    const parsed = JSON.parse(stored) as Partial<AIProviderConfig> & { model?: string };
    const provider = parsed.provider || defaultConfig.provider;
    return {
      provider,
      apiKey: '',
      baseUrl: '',
      selectedModel: parsed.selectedModel || parsed.model || '',
    };
  } catch {
    return defaultConfig;
  }
}

export const useUIStore = create<UIState>((set, get) => ({
  darkMode: readInitialTheme() === 'dark',
  language: readInitialLanguage(),
  lowDataMode: localStorage.getItem('low_data_mode') === 'true',
  aiChatOpen: false,
  aiSettingsOpen: false,
  aiProviderConfig: readConfig(),
  currentRoute: window.location.pathname,
  setDarkMode: (darkMode) => {
    const theme: ThemeName = darkMode ? 'dark' : 'light';
    localStorage.setItem('theme', theme);
    applyTheme(theme);
    set({ darkMode });
  },
  toggleDarkMode: () => get().setDarkMode(!get().darkMode),
  setLanguage: (language) => {
    if (!isAppLanguage(language)) return;
    localStorage.setItem('app_language', language);
    set({ language });
  },
  setLowDataMode: (enabled) => {
    localStorage.setItem('low_data_mode', String(enabled));
    set({ lowDataMode: enabled });
  },
  setAiChatOpen: (aiChatOpen) => set({ aiChatOpen }),
  setAiSettingsOpen: (aiSettingsOpen) => set({ aiSettingsOpen }),
  setAiProviderConfig: (aiProviderConfig) => {
    const normalized = {
      provider: aiProviderConfig.provider,
      apiKey: '',
      baseUrl: '',
      selectedModel: aiProviderConfig.selectedModel || '',
    };
    localStorage.setItem('ai_provider_config', JSON.stringify(normalized));
    set({ aiProviderConfig: normalized });
  },
  setCurrentRoute: (route) => {
    window.history.pushState(null, '', route);
    set({ currentRoute: route });
  },
}));
