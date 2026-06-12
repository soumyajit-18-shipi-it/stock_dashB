import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';
import en from './locales/en/translation.json';
import hi from './locales/hi/translation.json';
import or from './locales/or/translation.json';
import de from './locales/de/translation.json';
import fr from './locales/fr/translation.json';

export const languages = [
  { code: 'en', label: 'English' },
  { code: 'hi', label: '\u0939\u093f\u0928\u094d\u0926\u0940' },
  { code: 'or', label: '\u0b13\u0b21\u0b3c\u0b3f\u0b06' },
  { code: 'de', label: 'Deutsch' },
  { code: 'fr', label: 'Fran\u00e7ais' },
] as const;

export type AppLanguage = (typeof languages)[number]['code'];

export const defaultLanguage: AppLanguage = 'en';

export function isAppLanguage(language: string | null): language is AppLanguage {
  return languages.some((item) => item.code === language);
}

export function readInitialLanguage(): AppLanguage {
  const stored = localStorage.getItem('app_language');
  return isAppLanguage(stored) ? stored : defaultLanguage;
}

i18n.use(initReactI18next).init({
  resources: {
    en: { translation: en },
    hi: { translation: hi },
    or: { translation: or },
    de: { translation: de },
    fr: { translation: fr },
  },
  lng: readInitialLanguage(),
  fallbackLng: 'en',
  interpolation: { escapeValue: false },
  returnNull: false,
});

export default i18n;
