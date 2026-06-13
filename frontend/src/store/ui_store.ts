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
  aiChatOpen: boolean;
  aiSettingsOpen: boolean;
  aiProviderConfig: AIProviderConfig;
  setDarkMode: (darkMode: boolean) => void;
  toggleDarkMode: () => void;
  setLanguage: (language: AppLanguage) => void;
  setAiChatOpen: (open: boolean) => void;
  setAiSettingsOpen: (open: boolean) => void;
  setAiProviderConfig: (config: AIProviderConfig) => void;
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
      apiKey: parsed.apiKey || '',
      baseUrl: parsed.baseUrl || (provider === 'ollama' ? defaultConfig.baseUrl : ''),
      selectedModel: parsed.selectedModel || parsed.model || '',
    };
  } catch {
    return defaultConfig;
  }
}

export const useUIStore = create<UIState>((set, get) => ({
  darkMode: readInitialTheme() === 'dark',
  language: readInitialLanguage(),
  aiChatOpen: false,
  aiSettingsOpen: false,
  aiProviderConfig: readConfig(),
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
  setAiChatOpen: (aiChatOpen) => set({ aiChatOpen }),
  setAiSettingsOpen: (aiSettingsOpen) => set({ aiSettingsOpen }),
  setAiProviderConfig: (aiProviderConfig) => {
    const normalized = {
      provider: aiProviderConfig.provider,
      apiKey: aiProviderConfig.apiKey || '',
      baseUrl: aiProviderConfig.baseUrl || (aiProviderConfig.provider === 'ollama' ? defaultConfig.baseUrl : ''),
      selectedModel: aiProviderConfig.selectedModel || '',
    };
    localStorage.setItem('ai_provider_config', JSON.stringify(normalized));
    set({ aiProviderConfig: normalized });
  },
}));
