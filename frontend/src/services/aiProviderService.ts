import type { AIProviderConfig } from '../store/ui_store';
import type { StockResponse } from '../types';
import { currencyForStock, formatCurrency } from '../utils/format';

export interface ChatMessage {
  role: 'system' | 'user' | 'assistant';
  content: string;
}

export interface ModelOption {
  id: string;
  name: string;
}

const REQUEST_TIMEOUT_MS = 15000;

export function isAIConfigured(config: AIProviderConfig): boolean {
  if (config.provider === 'ollama') return Boolean(config.baseUrl && config.selectedModel);
  if (config.provider === 'auto') return Boolean(config.apiKey && config.selectedModel);
  if (config.provider === 'custom') return Boolean(config.baseUrl && config.selectedModel);
  return Boolean(config.apiKey && config.selectedModel);
}

export function providerLabelKey(provider: AiProvider) {
  return `provider${provider.charAt(0).toUpperCase()}${provider.slice(1)}`;
}

export function defaultBaseUrl(provider: AiProvider) {
  if (provider === 'ollama') return 'http://localhost:11434';
  if (provider === 'custom') return '';
  return '';
}

function withTimeout(signal?: AbortSignal | null, timeoutMs = REQUEST_TIMEOUT_MS) {
  const controller = new AbortController();
  let timedOut = false;
  const timeout = window.setTimeout(() => {
    timedOut = true;
    controller.abort(new DOMException('Timeout', 'TimeoutError'));
  }, timeoutMs);
  const abort = () => controller.abort(signal?.reason);
  signal?.addEventListener('abort', abort, { once: true });
  return {
    signal: controller.signal,
    get timedOut() {
      return timedOut;
    },
    cleanup: () => {
      window.clearTimeout(timeout);
      signal?.removeEventListener('abort', abort);
    },
  };
}

async function checkedFetch(input: RequestInfo | URL, init: RequestInit = {}, timeoutMs = REQUEST_TIMEOUT_MS) {
  const wrapped = withTimeout(init.signal, timeoutMs);
  try {
    const response = await fetch(input, { ...init, signal: wrapped.signal });
    if (!response.ok) {
      const text = await response.text().catch(() => '');
      throw new Error(readableProviderError(response.status, text));
    }
    return response;
  } catch (error) {
    if (wrapped.timedOut) throw new Error('Timeout');
    throw error;
  } finally {
    wrapped.cleanup();
  }
}

function readableProviderError(status: number, body: string) {
  let parsedMsg = '';
  if (body) {
    try {
      const parsed = JSON.parse(body);
      parsedMsg = parsed.error?.message || parsed.message || parsed.detail || '';
    } catch {
      parsedMsg = body.slice(0, 180);
    }
  }

  if (parsedMsg) {
    const lowerMsg = parsedMsg.toLowerCase();
    if (lowerMsg.includes('terms') || lowerMsg.includes('unavailable') || lowerMsg.includes('not found') || lowerMsg.includes('does not exist')) {
      return `This model is unavailable. Please select another model.`;
    }
    return parsedMsg;
  }

  if (status === 401 || status === 403) return 'Invalid API key or unauthorized provider access.';
  if (status === 429) return 'Provider quota exceeded. Try again later.';
  
  return `Provider request failed (${status}).`;
}

function normalizeBaseUrl(baseUrl = '') {
  return baseUrl.replace(/\/$/, '');
}

function normalizeModelList(data: unknown): ModelOption[] {
  const raw = Array.isArray((data as { data?: unknown[] }).data)
    ? (data as { data: unknown[] }).data
    : Array.isArray((data as { models?: unknown[] }).models)
      ? (data as { models: unknown[] }).models
      : Array.isArray(data)
        ? data as unknown[]
        : [];
  return raw.map((item) => {
    const model = item as { id?: string; name?: string; model?: string; display_name?: string };
    const id = model.id || model.name || model.model || '';
    return { id, name: model.display_name || model.name || model.model || id };
  }).filter((model) => model.id);
}

export type AiProvider = 'ollama' | 'openai' | 'gemini' | 'anthropic' | 'custom' | 'auto';

export interface ProviderMeta {
  provider: AiProvider;
  baseUrl?: string;
}

export function detectProviderFromKey(apiKey: string): ProviderMeta {
  if (!apiKey) return { provider: 'openai', baseUrl: 'https://api.openai.com/v1' };
  
  // Specific detections
  if (apiKey.startsWith('sk-ant-')) return { provider: 'anthropic' };
  if (apiKey.startsWith('AIza')) return { provider: 'gemini' };
  if (apiKey.startsWith('gsk_')) return { provider: 'openai', baseUrl: 'https://api.groq.com/openai/v1' };
  if (apiKey.startsWith('sk-or-v1-')) return { provider: 'openai', baseUrl: 'https://openrouter.ai/api/v1' };
  
  // Generic OpenAI-compatible detection (OpenAI, DeepInfra, Together, etc. often use sk-)
  if (apiKey.startsWith('sk-')) return { provider: 'openai', baseUrl: 'https://api.openai.com/v1' };
  
  // Default to auto (which will likely try OpenAI compatible)
  return { provider: 'openai', baseUrl: 'https://api.openai.com/v1' };
}

export async function fetchModels(config: AIProviderConfig, signal?: AbortSignal): Promise<ModelOption[]> {
  const meta = config.provider === 'auto' ? detectProviderFromKey(config.apiKey || '') : { provider: config.provider, baseUrl: config.baseUrl };
  const provider = meta.provider;
  const baseUrl = normalizeBaseUrl(meta.baseUrl || config.baseUrl || '');

  if (provider === 'ollama') {
    const ollamaUrl = baseUrl || 'http://localhost:11434';
    try {
      const response = await checkedFetch(`${ollamaUrl}/api/tags`, { signal });
      return normalizeModelList(await response.json());
    } catch (error) {
      if (error instanceof TypeError || (error instanceof Error && error.message === 'Failed to fetch')) {
        throw new Error('Ollama server not detected.\nStart Ollama and try again.');
      }
      throw error;
    }
  }

  if (provider === 'gemini') {
    if (!config.apiKey) throw new Error('API key is required.');
    const response = await checkedFetch(`https://generativelanguage.googleapis.com/v1/models?key=${encodeURIComponent(config.apiKey)}`, { signal });
    return normalizeModelList(await response.json()).map((model) => ({
      id: model.id.replace(/^models\//, ''),
      name: model.name.replace(/^models\//, ''),
    }));
  }

  if (provider === 'anthropic') {
    if (!config.apiKey) throw new Error('API key is required.');
    // Note: Anthropic models list endpoint might require specific headers or might not be publicly listable without auth
    // For now, let's try their standard models if listing fails or just return common ones
    try {
      const response = await checkedFetch('https://api.anthropic.com/v1/models', {
        headers: {
          'x-api-key': config.apiKey,
          'anthropic-version': '2023-06-01',
          'anthropic-dangerous-direct-browser-access': 'true',
        },
        signal,
      });
      return normalizeModelList(await response.json());
    } catch {
      return [
        { id: 'claude-3-5-sonnet-20240620', name: 'Claude 3.5 Sonnet' },
        { id: 'claude-3-opus-20240229', name: 'Claude 3 Opus' },
        { id: 'claude-3-haiku-20240307', name: 'Claude 3 Haiku' },
      ];
    }
  }

  // Fallback to generic OpenAI-compatible models endpoint
  if (!config.apiKey && provider !== 'custom') throw new Error('API key is required.');
  const modelsUrl = baseUrl ? `${baseUrl}/models` : 'https://api.openai.com/v1/models';
  
  try {
    const response = await checkedFetch(modelsUrl, {
      headers: { Authorization: `Bearer ${config.apiKey}` },
      signal,
    });
    return normalizeModelList(await response.json());
  } catch (error) {
    if (provider === 'auto' && baseUrl !== 'https://api.openai.com/v1') {
      // If auto detection with a specific baseUrl failed, try generic OpenAI
      const retryResponse = await checkedFetch('https://api.openai.com/v1/models', {
        headers: { Authorization: `Bearer ${config.apiKey}` },
        signal,
      });
      return normalizeModelList(await retryResponse.json());
    }
    throw error;
  }
}

export function selectBestModel(_provider: AiProvider, models: ModelOption[]) {
  // Try to find a sensible default
  const priorities = ['gpt-4o', 'gpt-4', 'claude-3-5-sonnet', 'claude-3', 'gemini-1.5-pro', 'gemini-1.5-flash', 'llama-3', 'llama3', 'mixtral', 'gemma', 'qwen', 'mistral'];
  for (const p of priorities) {
    const found = models.find(m => m.id.toLowerCase().includes(p));
    if (found) return found;
  }
  return models[0];
}

export async function detectAndApplyModel(config: AIProviderConfig, signal?: AbortSignal): Promise<AIProviderConfig> {
  const models = await fetchModels(config, signal);
  const selected = selectBestModel(config.provider, models);
  return { ...config, selectedModel: selected?.id || config.selectedModel || '' };
}

export async function testConnection(config: AIProviderConfig, signal?: AbortSignal) {
  await fetchModels(config, signal);
  return true;
}

function buildSystemPrompt(stock: StockResponse, language: string): string {
  const currency = currencyForStock(stock);
  const candles = stock.history.slice(-8);
  return [
    'You are a stock analysis assistant. Do not provide financial advice.',
    `Respond in language code: ${language}.`,
    `Ticker: ${stock.profile.ticker}`,
    `Company: ${stock.profile.name || stock.profile.ticker}`,
    `Current price: ${formatCurrency(stock.profile.current_price, currency)}`,
    `Prediction: ${formatCurrency(stock.prediction.predicted_price, currency)}, trend ${stock.prediction.trend}, confidence ${Math.round(stock.prediction.confidence * 100)}%.`,
    `Indicators: RMSE ${stock.metrics.rmse}, MAE ${stock.metrics.mae}, R2 ${stock.metrics.r2}.`,
    `Last candles: ${JSON.stringify(candles)}`,
  ].join('\n');
}

async function parseSseStream(response: Response, onEvent: (data: string) => void) {
  const reader = response.body?.getReader();
  if (!reader) return;
  const decoder = new TextDecoder();
  let buffer = '';
  while (true) {
    const { value, done } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split('\n');
    buffer = lines.pop() || '';
    for (const line of lines) {
      const trimmed = line.trim();
      if (!trimmed || !trimmed.startsWith('data:')) continue;
      const data = trimmed.slice(5).trim();
      if (data === '[DONE]') return;
      onEvent(data);
    }
  }
  const trailing = buffer.trim();
  if (trailing.startsWith('data:')) {
    const data = trailing.slice(5).trim();
    if (data && data !== '[DONE]') onEvent(data);
  }
}

async function parseOpenAIStream(response: Response, onToken: (token: string) => void) {
  await parseSseStream(response, (data) => {
    try {
      const json = JSON.parse(data);
      const token = json.choices?.[0]?.delta?.content || json.delta?.text || '';
      if (token) onToken(token);
    } catch {
      // Ignore keepalive or malformed chunks
    }
  });
}

async function parseJsonLineStream(response: Response, onToken: (token: string) => void) {
  const reader = response.body?.getReader();
  if (!reader) return;
  const decoder = new TextDecoder();
  let buffer = '';
  while (true) {
    const { value, done } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split('\n');
    buffer = lines.pop() || '';
    for (const line of lines) {
      if (!line.trim()) continue;
      try {
        const json = JSON.parse(line);
        const token = json.message?.content || json.response || '';
        if (token) onToken(token);
      } catch {
        // Ignore malformed fragments.
      }
    }
  }
  if (buffer.trim()) {
    try {
      const json = JSON.parse(buffer.trim());
      const token = json.message?.content || json.response || '';
      if (token) onToken(token);
    } catch {
      // Ignore malformed trailing fragments.
    }
  }
}

export async function streamChat(config: AIProviderConfig, messages: ChatMessage[], signal: AbortSignal, onToken: (token: string) => void) {
  let effective = config.selectedModel ? config : await detectAndApplyModel(config, signal);
  if (!effective.selectedModel) throw new Error('No model available for selected provider.');

  const attemptStream = async (currentConfig: AIProviderConfig) => {
    const meta = currentConfig.provider === 'auto' ? detectProviderFromKey(currentConfig.apiKey || '') : { provider: currentConfig.provider, baseUrl: currentConfig.baseUrl };
    const provider = meta.provider;
    const baseUrl = normalizeBaseUrl(meta.baseUrl || currentConfig.baseUrl || '');

    if (provider === 'ollama') {
      const ollamaUrl = baseUrl || 'http://localhost:11434';
      let response: Response;
      try {
        response = await checkedFetch(`${ollamaUrl}/api/chat`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ model: currentConfig.selectedModel, messages, stream: true }),
          signal,
        }, 120000);
      } catch (error) {
        if (error instanceof TypeError || (error instanceof Error && error.message === 'Failed to fetch')) {
          throw new Error('Ollama server not detected.\nStart Ollama and try again.');
        }
        throw error;
      }
      await parseJsonLineStream(response, onToken);
      return;
    }

    if (provider === 'gemini') {
      const response = await checkedFetch(`https://generativelanguage.googleapis.com/v1beta/models/${currentConfig.selectedModel}:streamGenerateContent?alt=sse&key=${encodeURIComponent(currentConfig.apiKey || '')}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          contents: messages.filter((m) => m.role !== 'system').map((m) => ({ role: m.role === 'assistant' ? 'model' : 'user', parts: [{ text: m.content }] })),
          systemInstruction: { parts: [{ text: messages.find((m) => m.role === 'system')?.content || '' }] },
        }),
        signal,
      }, 120000);
      await parseSseStream(response, (chunk) => {
        try {
          const text = JSON.parse(chunk).candidates?.[0]?.content?.parts?.[0]?.text;
          if (text) onToken(text);
        } catch {
          if (chunk) onToken(chunk);
        }
      });
      return;
    }

    if (provider === 'anthropic') {
      const system = messages.find((m) => m.role === 'system')?.content || '';
      const response = await checkedFetch('https://api.anthropic.com/v1/messages', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'x-api-key': currentConfig.apiKey || '',
          'anthropic-version': '2023-06-01',
          'anthropic-dangerous-direct-browser-access': 'true',
        },
        body: JSON.stringify({
          model: currentConfig.selectedModel,
          max_tokens: 1400,
          stream: true,
          system,
          messages: messages.filter((m) => m.role !== 'system'),
        }),
        signal,
      }, 120000);
      await parseSseStream(response, (chunk) => {
        try {
          const json = JSON.parse(chunk);
          const token = json.delta?.text || json.content_block_delta?.delta?.text || '';
          if (token) onToken(token);
        } catch {
          // Ignore non-content events.
        }
      });
      return;
    }

    const chatUrl = baseUrl ? `${baseUrl}/chat/completions` : 'https://api.openai.com/v1/chat/completions';
    const response = await checkedFetch(chatUrl, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${currentConfig.apiKey || ''}` },
      body: JSON.stringify({ model: currentConfig.selectedModel, messages, stream: true }),
      signal,
    }, 120000);
    await parseOpenAIStream(response, onToken);
  };

  try {
    await attemptStream(effective);
  } catch (error) {
    if (error instanceof Error && error.message.includes('unavailable. Please select another model')) {
      // Auto-fallback
      effective = await detectAndApplyModel({ ...config, selectedModel: '' }, signal);
      if (!effective.selectedModel) throw new Error('No available models found to fallback to.');
      await attemptStream(effective);
    } else {
      throw error;
    }
  }
}



export function buildChatMessages(stock: StockResponse, language: string, userMessages: ChatMessage[]) {
  return [{ role: 'system' as const, content: buildSystemPrompt(stock, language) }, ...userMessages];
}

export async function generateReport(config: AIProviderConfig, stock: StockResponse, language: string, signal: AbortSignal, onToken: (token: string) => void) {
  // Use a shorter prompt for faster generation
  const shorterPrompt = `Create a brief stock analysis report for ${stock.profile.ticker}: Price Analysis, Prediction, Technical Overview, Risks, Recommendation. Be extremely concise.`;
  await streamChat(config, [
    { role: 'system', content: buildSystemPrompt(stock, language) },
    { role: 'user', content: shorterPrompt },
  ], signal, onToken);
}







