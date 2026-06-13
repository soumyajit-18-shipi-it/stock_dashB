import { useEffect, useMemo, useRef, useState } from 'react';
import { createPortal } from 'react-dom';
import { X } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { useUIStore, type AIProviderConfig } from '../store/ui_store';
import { fetchModels, selectBestModel, testConnection, type ModelOption } from '../services/aiProviderService';

const providerOptions: { value: 'ollama' | 'auto'; labelKey: string }[] = [
  { value: 'ollama', labelKey: 'providerOllama' },
  { value: 'auto', labelKey: 'Auto-Detect / App Default' },
];

function canFetchModels(config: AIProviderConfig) {
  if (config.provider === 'ollama') return Boolean(config.baseUrl);
  // Auto-detect is always available because it fallbacks to backend
  return true;
}

export function AISettingsModal() {
  const { t } = useTranslation();
  const { aiSettingsOpen, setAiSettingsOpen, aiProviderConfig, setAiProviderConfig } = useUIStore();
  
  // Initialize form with auto-provider if it was something else (migration)
  const initialForm = useMemo(() => {
    if (aiProviderConfig.provider !== 'ollama' && aiProviderConfig.provider !== 'auto') {
      return { ...aiProviderConfig, provider: 'auto' as const };
    }
    return aiProviderConfig;
  }, [aiProviderConfig]);

  const [form, setForm] = useState<AIProviderConfig>(initialForm);
  const [status, setStatus] = useState('');
  const [testing, setTesting] = useState(false);
  const [detecting, setDetecting] = useState(false);
  const [models, setModels] = useState<ModelOption[]>([]);
  const mountedRef = useRef(false);

  useEffect(() => {
    mountedRef.current = true;
    return () => {
      mountedRef.current = false;
    };
  }, []);

  useEffect(() => {
    if (aiSettingsOpen) {
      setForm(initialForm);
      setModels([]);
      setStatus('');
    }
  }, [initialForm, aiSettingsOpen]);

  const update = (patch: Partial<AIProviderConfig>) => setForm((current) => ({ ...current, ...patch }));

  useEffect(() => {
    if (!aiSettingsOpen || !canFetchModels(form)) {
      setModels([]);
      return;
    }

    const controller = new AbortController();
    const timeout = window.setTimeout(async () => {
      setDetecting(true);
      setStatus('');
      try {
        const names = await fetchModels(form, controller.signal);
        if (!mountedRef.current || controller.signal.aborted) return;
        setModels(names);
        
        // If no model is selected or the current selected model isn't in the new list, pick the best one
        const currentModelExists = names.some(m => m.id === form.selectedModel);
        if (!form.selectedModel || !currentModelExists) {
          const best = selectBestModel(form.provider, names);
          if (best) {
            setForm(current => ({ ...current, selectedModel: best.id }));
          }
        }
      } catch (error) {
        if (!mountedRef.current || controller.signal.aborted) return;
        setModels([]);
        const message = error instanceof Error ? error.message : t('connectionFailed');
        setStatus(message);
      } finally {
        if (mountedRef.current && !controller.signal.aborted) setDetecting(false);
      }
    }, 500);

    return () => {
      window.clearTimeout(timeout);
      controller.abort();
    };
  }, [aiSettingsOpen, form.provider, form.apiKey, form.baseUrl, t]);

  if (!aiSettingsOpen) return null;

  const handleProviderChange = (value: 'ollama' | 'auto') => {
    setForm({
      provider: value,
      apiKey: form.apiKey || '',
      baseUrl: value === 'ollama' ? 'http://localhost:11434' : '',
      selectedModel: '',
    });
    setModels([]);
    setStatus('');
  };

  const handleSave = () => {
    setAiProviderConfig(form);
    setAiSettingsOpen(false);
  };

  const handleTest = async () => {
    const controller = new AbortController();
    setTesting(true);
    setStatus('');
    try {
      await testConnection(form, controller.signal);
      if (mountedRef.current) setStatus(t('connected'));
    } catch (error) {
      const message = error instanceof Error ? error.message : t('connectionFailed');
      if (mountedRef.current) setStatus(message === 'Timeout' ? t('timeout') : `${t('connectionFailed')}: ${message}`);
    } finally {
      if (mountedRef.current) setTesting(false);
    }
  };

  return createPortal(
    <div className="fixed inset-0 z-[100] flex items-center justify-center bg-slate-950/80 p-4">
      <div className="w-full max-w-lg rounded-xl border border-slate-700 bg-slate-900 p-6 shadow-2xl">
        <div className="mb-5 flex items-center justify-between">
          <h2 className="text-xl font-semibold text-white">{t('settingsTitle')}</h2>
          <button onClick={() => setAiSettingsOpen(false)} className="rounded-lg p-2 text-slate-400 hover:bg-slate-800 hover:text-white" aria-label={t('cancel')}>
            <X className="h-5 w-5" />
          </button>
        </div>

        <div className="space-y-6">
          <div className="grid grid-cols-2 gap-2 p-1 bg-slate-800 rounded-lg">
            {providerOptions.map((opt) => (
              <button
                key={opt.value}
                onClick={() => handleProviderChange(opt.value)}
                className={`px-4 py-2 rounded-md text-sm font-medium transition-all ${
                  form.provider === opt.value
                    ? 'bg-emerald-600 text-white shadow-lg'
                    : 'text-slate-400 hover:text-white'
                }`}
              >
                {opt.value === 'auto' ? opt.labelKey : t(opt.labelKey)}
              </button>
            ))}
          </div>

          {form.provider === 'ollama' ? (
            <label className="block animate-in fade-in slide-in-from-top-2">
              <span className="mb-1 block text-sm text-slate-300">{t('baseUrl')}</span>
              <input 
                value={form.baseUrl || ''} 
                onChange={(e) => update({ baseUrl: e.target.value, selectedModel: '' })} 
                className="w-full rounded-lg border border-slate-700 bg-slate-800 px-3 py-2 text-white focus:border-emerald-500 focus:outline-none transition-colors"
                placeholder="http://localhost:11434"
              />
            </label>
          ) : (
            <div className="space-y-4 animate-in fade-in slide-in-from-top-2">
              <label className="block">
                <span className="mb-1 block text-sm text-slate-300">API Key (Optional)</span>
                <input 
                  type="password" 
                  value={form.apiKey || ''} 
                  onChange={(e) => update({ apiKey: e.target.value, selectedModel: '' })} 
                  className="w-full rounded-lg border border-slate-700 bg-slate-800 px-3 py-2 text-white focus:border-emerald-500 focus:outline-none transition-colors"
                  placeholder="Paste your API key or leave blank for App Default"
                />
                <p className="mt-2 text-xs text-slate-400">If blank, the application will use its default provider (Groq/Llama-3).</p>
              </label>
              
              <label className="block">
                <span className="mb-1 block text-sm text-slate-300">Custom Endpoint (Optional)</span>
                <input 
                  type="text" 
                  value={form.baseUrl || ''} 
                  onChange={(e) => update({ baseUrl: e.target.value, selectedModel: '' })} 
                  className="w-full rounded-lg border border-slate-700 bg-slate-800 px-3 py-2 text-white focus:border-emerald-500 focus:outline-none transition-colors"
                  placeholder="e.g. https://api.together.xyz/v1"
                />
                <p className="mt-2 text-xs text-slate-400">Advanced: Use for custom OpenAI-compatible providers.</p>
              </label>
            </div>
          )}

          <div className="rounded-lg border border-slate-700 bg-slate-800/50 p-4">
            <div className="flex items-center justify-between mb-2">
              <p className="text-sm text-slate-300">{t('selectedModel')}</p>
              {detecting && <div className="w-4 h-4 border-2 border-emerald-500 border-t-transparent rounded-full animate-spin" />}
            </div>
            {models.length > 0 ? (
              <select value={form.selectedModel || ''} onChange={(e) => update({ selectedModel: e.target.value })} className="w-full rounded-lg border border-slate-700 bg-slate-800 px-3 py-2 text-white focus:border-emerald-500 focus:outline-none transition-colors">
                {models.map((model) => <option key={model.id} value={model.id}>{model.name}</option>)}
              </select>
            ) : (
              <p className="mt-1 text-sm font-medium text-white italic">{detecting ? t('detectingModels') : form.selectedModel || t('notAvailable')}</p>
            )}
            <p className="mt-2 text-xs text-slate-400">Models are detected automatically from your provider.</p>
          </div>

          {status && (
            <div className={`p-3 rounded-lg text-sm ${status.includes('success') || status.includes(t('connected')) ? 'bg-emerald-500/10 text-emerald-400' : 'bg-red-500/10 text-red-400'}`}>
              {status}
            </div>
          )}
        </div>

        <div className="mt-8 flex justify-end gap-3">
          <button onClick={handleTest} disabled={testing || detecting || !canFetchModels(form)} className="rounded-lg bg-slate-700 px-4 py-2 text-white hover:bg-slate-600 disabled:opacity-50 transition-colors">{testing ? t('testing') : t('testConnection')}</button>
          <button onClick={handleSave} disabled={detecting} className="rounded-lg bg-emerald-600 px-6 py-2 font-semibold text-white hover:bg-emerald-700 disabled:opacity-50 transition-colors shadow-lg shadow-emerald-900/20">{t('save')}</button>
        </div>
      </div>
    </div>,
    document.body,
  );
}


