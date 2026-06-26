import { currencyForStock, formatCurrency } from '../utils/format';

import type { AIProviderConfig } from '../store/ui_store';
import type { StockResponse } from '../types';

export interface ChatMessage {
  role: 'system' | 'user' | 'assistant';
  content: string;
}

export interface ModelOption {
  id: string;
  name: string;
}

export interface AIHealth {
  configured: boolean;
  provider: string | null;
  model?: string;
  streaming_supported?: boolean;
  report_generation_supported?: boolean;
  checked_at?: string;
  error?: string;
  code?: string;
}

const REQUEST_TIMEOUT_MS = 60000; // Increased to 60s as per user request
const VITE_API_URL = import.meta.env.VITE_API_URL;
const API_BASE_URL =
  VITE_API_URL && VITE_API_URL !== '/api/v1'
    ? VITE_API_URL
    : typeof window !== 'undefined' &&
      (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1')
    ? 'http://localhost:8000/api/v1'
    : '/api/v1';

export function isAIConfigured(config: AIProviderConfig): boolean {
  return config.provider === 'auto' || config.provider === 'ollama' || Boolean(config.provider);
}

export function providerLabelKey(provider: AiProvider) {
  return `provider${provider.charAt(0).toUpperCase()}${provider.slice(1)}`;
}

export function defaultBaseUrl(provider: AiProvider) {
  if (provider === 'ollama') return 'http://localhost:11434';
  return '';
}

function withTimeout(signal?: AbortSignal | null, timeoutMs = REQUEST_TIMEOUT_MS) {
  const controller = new AbortController();
  const timeout = setTimeout(() => {
    controller.abort(new Error('AbortError'));
  }, timeoutMs);

  if (signal) {
    signal.addEventListener('abort', () => {
      clearTimeout(timeout);
      controller.abort();
    });
  }

  return {
    signal: controller.signal,
    cleanup: () => clearTimeout(timeout),
  };
}

async function checkedFetch(input: string, init: RequestInit = {}, timeoutMs = REQUEST_TIMEOUT_MS) {
  const { signal, cleanup } = withTimeout(init.signal, timeoutMs);
  try {
    const response = await fetch(input, { ...init, signal });
    if (!response.ok) {
      const text = await response.text().catch(() => '');
      console.error(`Fetch error ${response.status}:`, text);
      throw new Error(readableProviderError(response.status, text));
    }
    return response;
  } catch (err: unknown) {
    const error = err as Error;
    if (error.name === 'AbortError' || error.message === 'AbortError') {
      throw new Error('Request timed out after 60 seconds');
    }
    throw error;
  } finally {
    cleanup();
  }
}

function readableProviderError(status: number, body: string) {
  let parsedMsg = '';
  let code = '';
  if (body) {
    try {
      const parsed = JSON.parse(body);
      const detail = parsed.detail && typeof parsed.detail === 'object' ? parsed.detail : parsed;
      parsedMsg = detail.error?.message || detail.error || detail.message || parsed.detail || '';
      code = detail.code || parsed.code || '';
    } catch {
      parsedMsg = body.slice(0, 200);
    }
  }

  if (code === 'AI_PROVIDER_NOT_CONFIGURED') {
    return 'AI provider is not configured on the backend. Set GROQ_API_KEY or DEFAULT_GROQ_API_KEY in Railway.';
  }
  if (code === 'AI_PROVIDER_CONNECTION_FAILED') return 'Unable to connect to the AI service.';
  if (code === 'AI_EMPTY_RESPONSE') return 'The AI response was empty. Please try again.';
  if (code === 'AI_PROVIDER_TIMEOUT') return 'The AI request timed out. Please try again.';

  if (status === 404) {
    return 'AI backend route not found (404). Please ensure the backend is deployed with the latest AI routes and VITE_API_URL is correct.';
  }
  if (status === 401 || status === 403) return 'Invalid API key or unauthorized access.';
  if (status === 429) return 'Rate limit exceeded. Try again later.';
  if (status >= 500) return `Backend error (${status}). The AI service might be down.`;

  return parsedMsg || `Request failed with status ${status}`;
}

export type AiProvider = 'ollama' | 'openai' | 'gemini' | 'anthropic' | 'custom' | 'auto';

export interface ProviderMeta {
  provider: AiProvider;
  baseUrl?: string;
}

export function detectProviderFromKey(apiKey: string): ProviderMeta {
  if (!apiKey) return { provider: 'auto' };

  if (apiKey.startsWith('sk-ant-')) return { provider: 'anthropic' };
  if (apiKey.startsWith('AIza')) return { provider: 'gemini' };
  if (apiKey.startsWith('gsk_'))
    return { provider: 'openai', baseUrl: 'https://api.groq.com/openai/v1' };
  if (apiKey.startsWith('sk-or-v1-'))
    return { provider: 'openai', baseUrl: 'https://openrouter.ai/api/v1' };

  return { provider: 'openai', baseUrl: 'https://api.openai.com/v1' };
}

export async function fetchAIHealth(signal?: AbortSignal): Promise<AIHealth> {
  const response = await checkedFetch(`${API_BASE_URL}/health/ai`, { signal }, 10000);
  return (await response.json()) as AIHealth;
}

export async function fetchModels(
  config: AIProviderConfig,
  signal?: AbortSignal
): Promise<ModelOption[]> {
  const provider = config.provider || 'auto';

  console.info(`Fetching models from backend for provider: ${provider}`);

  // Use backend proxy
  try {
    const params = new URLSearchParams();
    params.append('provider', provider);

    const url = `${API_BASE_URL}/ai/models?${params.toString()}`;
    console.info(`Backend model fetch: ${url}`);
    const response = await checkedFetch(url, { signal });
    return await response.json();
  } catch (error) {
    console.error('Failed to fetch models from backend proxy:', error);
    return [
      { id: 'llama-3.3-70b-versatile', name: 'Llama 3.3 70B (Groq)' },
      { id: 'gpt-4o-mini', name: 'GPT-4o Mini (OpenAI)' },
      { id: 'claude-3-5-sonnet-20240620', name: 'Claude 3.5 Sonnet (Anthropic)' },
    ];
  }
}

export function selectBestModel(_provider: AiProvider, models: ModelOption[]) {
  const priorities = [
    'gpt-4o',
    'gpt-4',
    'claude-3-5-sonnet',
    'claude-3',
    'gemini-1.5-pro',
    'gemini-1.5-flash',
    'llama-3.3-70b',
    'llama-3.1-70b',
    'llama-3',
    'llama3',
    'mixtral',
    'gemma',
    'qwen',
    'mistral',
  ];
  for (const p of priorities) {
    const found = models.find((m) => m.id.toLowerCase().includes(p));
    if (found) return found;
  }
  return models[0];
}

export async function detectAndApplyModel(
  config: AIProviderConfig,
  signal?: AbortSignal
): Promise<AIProviderConfig> {
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
  const candles = stock.history.slice(-15);
  return [
    'You are a senior equity research analyst. Your task is to provide a professional, detailed, and data-driven stock analysis report.',
    'Follow these guidelines:',
    '1. Use a professional, objective tone.',
    '2. Use the provided stock data and technical indicators. Do not hallucinate data.',
    '3. Format your response using clear section headers.',
    '4. Provide detailed explanations for each section.',
    '5. Do not include markdown artifacts like excessive asterisks or raw symbols in the final output text.',
    `Respond in language: ${language}.`,
    '',
    `Ticker: ${stock.profile.ticker}`,
    `Company: ${stock.profile.name || stock.profile.ticker}`,
    `Exchange: ${stock.profile.exchange}`,
    `Sector: ${stock.profile.sector}`,
    `Industry: ${stock.profile.industry}`,
    `Current Price: ${formatCurrency(stock.profile.current_price, currency)}`,
    `Prediction: ${formatCurrency(stock.prediction.predicted_price, currency)}, trend ${stock.prediction.trend}, confidence ${Math.round(stock.prediction.confidence * 100)}%.`,
    `Metrics: RMSE ${stock.metrics.rmse}, MAE ${stock.metrics.mae}, R2 ${stock.metrics.r2}.`,
    `Recent History: ${JSON.stringify(candles)}`,
  ].join('\n');
}

async function parseSseStream(response: Response, onEvent: (data: string) => void) {
  if (!response.body) {
    throw new Error(`AI stream response has no body (status ${response.status})`);
  }
  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = '';
  while (true) {
    const { value, done } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split('\n');
    buffer = lines.pop() || '';
    for (const line of lines) {
      const trimmed = line.replace(/\r$/, '').trim();
      if (!trimmed || !trimmed.startsWith('data:')) continue;
      const data = trimmed.slice(5).trim();
      if (data === '[DONE]') return;
      onEvent(data);
    }
  }
}

async function parseOpenAIStream(
  response: Response,
  onToken: (token: string) => void,
): Promise<{ tokenCount: number; error: string }> {
  let tokenCount = 0;
  let streamError = '';
  await parseSseStream(response, (data) => {
    let json: {
      error?: unknown;
      choices?: { delta?: { content?: string } }[];
      delta?: { text?: string };
    };
    try {
      json = JSON.parse(data);
    } catch {
      if (data.includes('AI provider is not configured')) {
        streamError = 'AI provider is not configured. Please set DEFAULT_GROQ_API_KEY or configure Ollama.';
      }
      return;
    }
    if (json.error) {
      if (typeof json.error === 'object' && json.error && 'message' in json.error) {
        streamError = String((json.error as { message?: unknown }).message || 'AI provider error');
      } else {
        streamError = String(json.error);
      }
      return;
    }
    const token = json.choices?.[0]?.delta?.content || json.delta?.text || '';
    if (token) {
      tokenCount += 1;
      onToken(token);
    }
  });
  return { tokenCount, error: streamError };
}

export async function streamChat(
  config: AIProviderConfig,
  messages: ChatMessage[],
  signal: AbortSignal,
  onToken: (token: string) => void
) {
  const provider = config.provider || 'auto';

  console.info(`Starting streamChat: provider=${provider}, model=${config.selectedModel}`);

  // Use backend proxy
  try {
    const url = `${API_BASE_URL}/ai/chat`;
    console.info(`Backend chat stream: ${url}`);
    const response = await checkedFetch(
      url,
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          messages,
          provider,
          model: config.selectedModel,
          stream: true,
        }),
        signal,
      },
      REQUEST_TIMEOUT_MS
    );

    const { tokenCount, error: streamError } = await parseOpenAIStream(response, onToken);
    if (streamError) {
      throw new Error(streamError);
    }
    if (tokenCount === 0) {
      throw new Error(
        'AI response was empty. Check provider configuration or try again.'
      );
    }
    console.info('Backend chat stream finished');
  } catch (error) {
    console.error('Backend proxy chat failed:', error);
    throw error;
  }
}

export function buildChatMessages(
  stock: StockResponse,
  language: string,
  userMessages: ChatMessage[]
) {
  return [
    { role: 'system' as const, content: buildSystemPrompt(stock, language) },
    ...userMessages,
  ];
}

export async function generateReport(
  config: AIProviderConfig,
  stock: StockResponse,
  language: string,
  signal: AbortSignal,
  onToken: (token: string) => void
) {
  const reportPrompt = [
    'Generate a PROFESSIONAL EQUITY RESEARCH REPORT. Do not use placeholders like "Not Available".',
    'Use the provided data to generate meaningful insights even if some metrics are missing.',
    '',
    'Structure the report into these EXACT sections, starting each with the bracketed title:',
    '',
    '[EXECUTIVE SUMMARY]',
    '2-3 paragraphs of high-level analysis, sentiment, and outlook.',
    '',
    '[COMPANY INFORMATION]',
    'Discuss the company business model, sector position, and recent corporate developments.',
    '',
    '[PRICE ANALYSIS]',
    'Analyze recent price action, support/resistance levels, and volume trends.',
    '',
    '[TECHNICAL ANALYSIS]',
    'Discuss RSI, Moving Averages, and other technical indicators based on the provided history.',
    '',
    '[PREDICTION ANALYSIS]',
    'Detail the ML prediction, confidence level, and historical model performance (RMSE/MAE).',
    '',
    '[BULLISH FACTORS]',
    'List at least 3 detailed bullish catalysts.',
    '',
    '[BEARISH FACTORS]',
    'List at least 3 detailed bearish risks or catalysts.',
    '',
    '[RISK ASSESSMENT]',
    'Discuss market volatility, macro risks, and specific company risks.',
    '',
    '[SCENARIO ANALYSIS]',
    'Outline Bull Case, Base Case, and Bear Case scenarios.',
    '',
    '[RECOMMENDATION]',
    'Provide a clear investment recommendation (Buy/Hold/Sell) with technical justification.',
    '',
    '[CONCLUSION]',
    'Final summary and closing thoughts.',
    '',
    'Constraint: Do not use raw markdown asterisks for bullets; use plain bullet points (•).',
    'Constraint: Ensure every section is populated with at least 150 words of high-quality analysis.',
  ].join('\n');

  await streamChat(
    config,
    [
      { role: 'system', content: buildSystemPrompt(stock, language) },
      { role: 'user', content: reportPrompt },
    ],
    signal,
    onToken
  );
}
