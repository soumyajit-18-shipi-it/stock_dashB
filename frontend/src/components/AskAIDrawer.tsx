import { Bot, Send, X, Copy, RefreshCcw, Square, Trash2, Download } from 'lucide-react';
import { useEffect, useRef, useState, memo } from 'react';
import { createPortal } from 'react-dom';
import { useTranslation } from 'react-i18next';

import {
  buildChatMessages,
  isAIConfigured,
  providerLabelKey,
  streamChat,
  type ChatMessage,
} from '../services/aiProviderService';
import { useUIStore } from '../store/ui_store';

import type { StockResponse } from '../types';

interface AskAIDrawerProps {
  stockData: StockResponse | null;
}

interface ChatConversation {
  ticker: string;
  messages: {
    role: 'user' | 'assistant';
    content: string;
    timestamp: number;
  }[];
}

interface UIMessage extends ChatMessage {
  id: string;
  timestamp: number;
}

function messageId() {
  return typeof crypto !== 'undefined' && 'randomUUID' in crypto
    ? crypto.randomUUID()
    : `${Date.now()}-${Math.random()}`;
}

function loadHistory(ticker: string): UIMessage[] {
  try {
    const stored = localStorage.getItem('ai_chat_history');
    if (!stored) return [];
    const histories = JSON.parse(stored);
    if (!Array.isArray(histories)) return [];
    const conversation = (histories as ChatConversation[]).find((h) => h.ticker === ticker);
    if (!conversation) return [];
    return conversation.messages.map((m) => ({
      id: messageId(),
      role: m.role,
      content: m.content,
      timestamp: m.timestamp,
    }));
  } catch (error) {
    console.error('Failed to load chat history:', error);
    return [];
  }
}

function saveHistory(ticker: string, messages: UIMessage[]) {
  try {
    const stored = localStorage.getItem('ai_chat_history');
    let histories = stored ? JSON.parse(stored) : [];
    if (!Array.isArray(histories)) histories = [];

    const filteredMessages = messages
      .filter((m) => m.role !== 'system' && m.content.trim())
      .map((m) => ({
        role: m.role as 'user' | 'assistant',
        content: m.content,
        timestamp: m.timestamp || Date.now(),
      }))
      .slice(-50); // Limit to last 50 messages per ticker

    const index = (histories as ChatConversation[]).findIndex((h) => h.ticker === ticker);
    if (index >= 0) {
      histories[index].messages = filteredMessages;
    } else {
      histories.push({ ticker, messages: filteredMessages });
    }
    localStorage.setItem('ai_chat_history', JSON.stringify(histories));
  } catch (error) {
    console.error('Failed to save chat history:', error);
  }
}

function TypingIndicator() {
  return (
    <div className="flex items-center gap-1.5 py-1 px-1" aria-hidden="true">
      <span className="typing-dot" />
      <span className="typing-dot" />
      <span className="typing-dot" />
    </div>
  );
}

const MarkdownMessage = memo(function MarkdownMessage({
  content,
  isStreaming,
}: {
  content: string;
  isStreaming?: boolean;
}) {
  if (!content && isStreaming) return <TypingIndicator />;

  const lines = content.split('\n');
  let inCodeBlock = false;
  let codeBlockContent = '';

  const renderLines = [];

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];
    if (line === undefined) continue;
    const key = `${i}-${line}`;

    if (line.startsWith('```')) {
      if (inCodeBlock) {
        renderLines.push(
          <div key={key} className="my-2 rounded-md bg-slate-900 p-3 overflow-x-auto">
            <code className="text-sm font-mono text-slate-300 whitespace-pre">
              {codeBlockContent}
            </code>
          </div>
        );
        inCodeBlock = false;
        codeBlockContent = '';
      } else {
        inCodeBlock = true;
      }
      continue;
    }

    if (inCodeBlock) {
      codeBlockContent += line + '\n';
      continue;
    }

    if (/^#{1,3}\s+/.test(line)) {
      renderLines.push(
        <p key={key} className="font-bold text-white text-base mt-2 mb-1">
          {line.replace(/^#{1,3}\s+/, '')}
        </p>
      );
      continue;
    }

    if (/^\s*[-*•]\s+/.test(line)) {
      const text = line.replace(/^\s*[-*•]\s+/, '');
      renderLines.push(
        <div key={key} className="flex gap-2 pl-1">
          <span className="text-emerald-500">•</span>
          <p className="flex-1">{renderFormattedText(text)}</p>
        </div>
      );
      continue;
    }

    if (/^\s*\d+\.\s+/.test(line)) {
      const match = line.match(/^\s*(\d+\.)\s+(.*)/);
      if (match) {
        const indexText = match[1];
        const contentText = match[2];
        if (indexText !== undefined && contentText !== undefined) {
          renderLines.push(
            <div key={key} className="flex gap-2 pl-1">
              <span className="text-emerald-500">{indexText}</span>
              <p className="flex-1">{renderFormattedText(contentText)}</p>
            </div>
          );
          continue;
        }
      }
    }

    if (line.startsWith('> ')) {
      renderLines.push(
        <blockquote
          key={key}
          className="border-l-2 border-emerald-500 pl-3 italic text-slate-300 my-1"
        >
          {renderFormattedText(line.substring(2))}
        </blockquote>
      );
      continue;
    }

    if (line.includes('|') && line.trim().startsWith('|')) {
      const cells = line
        .split('|')
        .filter(Boolean)
        .map((c) => c.trim());
      if (!line.includes('---')) {
        renderLines.push(
          <div key={key} className="flex gap-4 border-b border-slate-700/50 py-1">
            {cells.map((cell, cIdx) => (
              <div key={`${key}-${cIdx}`} className="flex-1 text-sm">
                {renderFormattedText(cell)}
              </div>
            ))}
          </div>
        );
      }
      continue;
    }

    if (line.trim() === '') {
      renderLines.push(<div key={key} className="h-2" />);
      continue;
    }

    renderLines.push(<p key={key}>{renderFormattedText(line)}</p>);
  }

  if (inCodeBlock && isStreaming) {
    renderLines.push(
      <div key="streaming-code" className="my-2 rounded-md bg-slate-900 p-3 overflow-x-auto">
        <code className="text-sm font-mono text-slate-300 whitespace-pre">{codeBlockContent}</code>
      </div>
    );
  }

  return (
    <div className="space-y-1.5 whitespace-pre-wrap break-words leading-relaxed">{renderLines}</div>
  );
});

function renderFormattedText(text: string) {
  const parts = text.split(/(\*\*.*?\*\*|\*.*?\*|_.*?_|`.*?`)/g);
  return parts.map((part, i) => {
    if (part.startsWith('**') && part.endsWith('**')) {
      return (
        <strong key={i} className="font-bold text-white">
          {part.slice(2, -2)}
        </strong>
      );
    }
    if (
      (part.startsWith('*') && part.endsWith('*')) ||
      (part.startsWith('_') && part.endsWith('_'))
    ) {
      return (
        <em key={i} className="italic">
          {part.slice(1, -1)}
        </em>
      );
    }
    if (part.startsWith('`') && part.endsWith('`')) {
      return (
        <code key={i} className="bg-slate-700 px-1 rounded text-xs font-mono">
          {part.slice(1, -1)}
        </code>
      );
    }
    return part;
  });
}

export function AskAIDrawer({ stockData }: AskAIDrawerProps) {
  const { t, i18n } = useTranslation();
  const { aiChatOpen, setAiChatOpen, setAiSettingsOpen, aiProviderConfig } = useUIStore();
  const [messages, setMessages] = useState<UIMessage[]>([]);
  const [input, setInput] = useState('');
  const [streaming, setStreaming] = useState(false);
  const [error, setError] = useState('');
  const abortRef = useRef<AbortController | null>(null);
  const mountedRef = useRef(true);
  const scrollRef = useRef<HTMLDivElement>(null);
  const currentTickerRef = useRef<string | null>(null);

  useEffect(() => {
    if (stockData?.profile.ticker) {
      if (currentTickerRef.current !== stockData.profile.ticker) {
        currentTickerRef.current = stockData.profile.ticker;
        const history = loadHistory(stockData.profile.ticker);
        setMessages(history);
      }
    }
  }, [stockData?.profile.ticker]);

  useEffect(() => {
    if (scrollRef.current) {
      const container = scrollRef.current;
      container.scrollTop = container.scrollHeight;
    }
  }, [messages, streaming]);

  useEffect(
    () => () => {
      mountedRef.current = false;
      if (abortRef.current) abortRef.current.abort();
    },
    []
  );

  if (!stockData) return null;

  const configured = isAIConfigured(aiProviderConfig);

  const ask = async (question: string, isRetry = false) => {
    if (!configured) {
      setAiSettingsOpen(true);
      return;
    }

    if (abortRef.current) abortRef.current.abort();
    const controller = new AbortController();
    abortRef.current = controller;

    let updatedMessages = [...messages];
    if (isRetry) {
      updatedMessages = updatedMessages.slice(0, -2);
    }

    const userMessage: UIMessage = {
      id: messageId(),
      role: 'user',
      content: question,
      timestamp: Date.now(),
    };
    const assistantId = messageId();
    const assistantMessage: UIMessage = {
      id: assistantId,
      role: 'assistant',
      content: '',
      timestamp: Date.now(),
    };

    updatedMessages = [...updatedMessages, userMessage];
    setMessages([...updatedMessages, assistantMessage]);

    saveHistory(stockData.profile.ticker, updatedMessages);

    const nextMessages = buildChatMessages(stockData, i18n.language, [
      ...updatedMessages
        .filter((m) => m.role !== 'system')
        .map(({ role, content }) => ({ role, content }) as ChatMessage),
    ]);

    setInput('');
    setError('');
    setStreaming(true);

    try {
      let fullContent = '';
      await streamChat(aiProviderConfig, nextMessages, controller.signal, (token) => {
        if (mountedRef.current && !controller.signal.aborted) {
          fullContent += token;
          setMessages((current) =>
            current.map((message) =>
              message.id === assistantId ? { ...message, content: fullContent } : message
            )
          );
        }
      });

      if (mountedRef.current && !controller.signal.aborted) {
        saveHistory(stockData.profile.ticker, [
          ...updatedMessages,
          { ...assistantMessage, content: fullContent },
        ]);
      }
    } catch (err) {
      if (mountedRef.current && !(err instanceof DOMException && err.name === 'AbortError')) {
        setError(err instanceof Error ? err.message : t('aiError'));
      }
    } finally {
      if (mountedRef.current && abortRef.current === controller) {
        setStreaming(false);
        abortRef.current = null;
      }
    }
  };

  const handleStop = () => {
    if (abortRef.current) {
      abortRef.current.abort();
      setStreaming(false);
      abortRef.current = null;
    }
  };

  const handleClear = () => {
    if (!stockData) return;
    setMessages([]);
    saveHistory(stockData.profile.ticker, []);
  };

  const handleExport = () => {
    if (!stockData || messages.length === 0) return;
    const text = messages
      .map(
        (m) =>
          `[${new Date(m.timestamp).toLocaleString()}] ${m.role.toUpperCase()}:\n${m.content}\n`
      )
      .join('\n---\n\n');
    const blob = new Blob([text], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${stockData.profile.ticker}_chat_export.txt`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const drawer = aiChatOpen ? (
    <div className="fixed inset-0 z-[90] bg-slate-950/50 sm:bg-transparent">
      <aside className="fixed bottom-0 right-0 top-0 flex w-full max-w-md flex-col border-l border-slate-700 bg-slate-900 shadow-2xl">
        <div className="flex items-center justify-between border-b border-slate-700 p-4">
          <div>
            <h2 className="font-semibold text-white">
              {t('askAboutTicker', { ticker: stockData.profile.ticker })}
            </h2>
            {configured && (
              <span className="mt-1 inline-flex items-center gap-1 rounded-full bg-emerald-500/15 px-2 py-0.5 text-xs text-emerald-300">
                {t('providerBadge', { provider: t(providerLabelKey(aiProviderConfig.provider)) })}
                {aiProviderConfig.selectedModel && (
                  <span className="opacity-60 text-[10px]">({aiProviderConfig.selectedModel})</span>
                )}
              </span>
            )}
          </div>
          <div className="flex gap-1 items-center">
            {messages.length > 0 && (
              <>
                <button
                  onClick={handleExport}
                  className="rounded-lg p-2 text-slate-400 hover:bg-slate-800 hover:text-white"
                  title="Export Conversation"
                >
                  <Download className="h-4 w-4" />
                </button>
                <button
                  onClick={handleClear}
                  className="rounded-lg p-2 text-slate-400 hover:bg-slate-800 hover:text-white"
                  title="Clear Chat"
                >
                  <Trash2 className="h-4 w-4" />
                </button>
              </>
            )}
            <button
              onClick={() => setAiChatOpen(false)}
              className="rounded-lg p-2 text-slate-400 hover:bg-slate-800 hover:text-white"
              aria-label={t('cancel')}
            >
              <X className="h-5 w-5" />
            </button>
          </div>
        </div>
        <div className="flex-1 space-y-3 overflow-y-auto p-4" ref={scrollRef}>
          {!configured ? (
            <div className="rounded-lg border border-slate-700 bg-slate-800/60 p-4 text-slate-300">
              <p>{t('configureAiState')}</p>
              <button
                onClick={() => setAiSettingsOpen(true)}
                className="mt-3 rounded-lg bg-emerald-600 px-3 py-2 text-sm font-medium text-white"
              >
                {t('configureAi')}
              </button>
            </div>
          ) : messages.length === 0 ? (
            <p className="text-sm text-slate-400">{t('aiDisclaimer')}</p>
          ) : (
            messages.map((message, idx) => {
              const prevMessage = idx > 0 ? messages[idx - 1] : undefined;
              return (
                <div
                  key={message.id}
                  className={`rounded-lg p-3 text-sm group ${message.role === 'user' ? 'ml-8 bg-emerald-600 text-white' : 'mr-8 bg-slate-800 text-slate-100 border border-slate-700'}`}
                >
                  <div className="flex justify-between items-start mb-1 opacity-60">
                    <span className="text-[10px] uppercase font-bold">
                      {message.role === 'user' ? 'You' : 'AI'}
                    </span>
                    <span className="text-[10px]">
                      {new Date(message.timestamp).toLocaleTimeString([], {
                        hour: '2-digit',
                        minute: '2-digit',
                      })}
                    </span>
                  </div>
                  <MarkdownMessage
                    content={message.content}
                    isStreaming={streaming && idx === messages.length - 1}
                  />
                  {message.role === 'assistant' && !streaming && (
                    <div className="mt-3 flex gap-3 opacity-0 transition-opacity group-hover:opacity-100">
                      <button
                        onClick={() => navigator.clipboard.writeText(message.content)}
                        className="flex items-center gap-1 text-[11px] text-slate-400 hover:text-white"
                        title="Copy Message"
                      >
                        <Copy className="h-3 w-3" /> Copy
                      </button>
                      {idx === messages.length - 1 && prevMessage && (
                        <button
                          onClick={() => ask(prevMessage.content, true)}
                          className="flex items-center gap-1 text-[11px] text-slate-400 hover:text-white"
                          title="Regenerate Response"
                        >
                          <RefreshCcw className="h-3 w-3" /> Regenerate
                        </button>
                      )}
                    </div>
                  )}
                </div>
              );
            })
          )}
          {error && (
            <div className="rounded-lg bg-red-500/10 border border-red-500/20 p-3 text-sm text-red-400">
              <p className="font-semibold mb-1">Error</p>
              <p>{error}</p>
            </div>
          )}
        </div>
        <form
          onSubmit={(e) => {
            e.preventDefault();
            if (input.trim() && !streaming) void ask(input.trim());
          }}
          className="flex gap-2 border-t border-slate-700 p-4"
        >
          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            disabled={streaming || !configured}
            placeholder={configured ? t('aiPlaceholder') : t('configureAi')}
            className="min-w-0 flex-1 rounded-lg border border-slate-700 bg-slate-800 px-3 py-2 text-white placeholder-slate-500"
          />
          {streaming ? (
            <button
              type="button"
              onClick={handleStop}
              className="rounded-lg bg-red-600 p-2 text-white hover:bg-red-700"
              aria-label={t('stop')}
            >
              <Square className="h-5 w-5" />
            </button>
          ) : (
            <button
              type="submit"
              disabled={!input.trim() || !configured}
              className="rounded-lg bg-emerald-600 p-2 text-white hover:bg-emerald-700 disabled:opacity-60"
              aria-label={t('send')}
            >
              <Send className="h-5 w-5" />
            </button>
          )}
        </form>
      </aside>
    </div>
  ) : null;

  return (
    <>
      <button
        onClick={() => setAiChatOpen(true)}
        className="fixed bottom-5 right-5 z-40 flex items-center gap-2 rounded-full bg-emerald-600 px-4 py-3 font-medium text-white shadow-xl hover:bg-emerald-700"
      >
        <Bot className="h-5 w-5" />
        {t('askAi')}
      </button>
      {drawer ? createPortal(drawer, document.body) : null}
    </>
  );
}
