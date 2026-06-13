import { useRef, useState } from 'react';
import { flushSync } from 'react-dom';
import html2canvas from 'html2canvas';
import jsPDF from 'jspdf';
import { FileText } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { generateReport, isAIConfigured } from '../services/aiProviderService';
import { useUIStore } from '../store/ui_store';
import type { StockResponse } from '../types';
import { currencyForStock } from '../utils/format';

interface AIReportButtonProps {
  stockData: StockResponse;
}

const sectionKeys = [
  'EXECUTIVE SUMMARY',
  'COMPANY INFORMATION',
  'PRICE ANALYSIS',
  'TECHNICAL ANALYSIS',
  'PREDICTION ANALYSIS',
  'BULLISH FACTORS',
  'BEARISH FACTORS',
  'RISK ASSESSMENT',
  'SCENARIO ANALYSIS',
  'RECOMMENDATION',
  'CONCLUSION',
] as const;

function extractSection(text: string, title: string) {
  const escapedTitle = title.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  const otherTitles = sectionKeys.filter(t => t !== title).map(t => t.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')).join('|');
  
  // More robust pattern matching for [TITLE], TITLE:, or just TITLE at start of line
  const pattern = new RegExp(`(?:^|\\n)\\s*(?:\\[)?${escapedTitle}(?:\\])?:?\\s*\\n+([\\s\\S]*?)(?=\\n\\s*(?:\\[)?(?:${otherTitles})(?:\\])?:?\\s*\\n|$)`, 'i');
  
  const match = pattern.exec(text);
  let content = match?.[1]?.trim() || '';
  
  if (!content) {
    // Fallback search if the section header doesn't have brackets
    const fallbackPattern = new RegExp(`${escapedTitle}:?\\s*\\n+([\\s\\S]*?)(?=\\n(?:${otherTitles})|$)`, 'i');
    const fallbackMatch = fallbackPattern.exec(text);
    content = fallbackMatch?.[1]?.trim() || '';
  }

  // Clean up markdown but preserve structure
  return content
    .replace(/#{1,6}\s?/g, '') // Remove headers
    .replace(/\*\*/g, '')      // Remove bold
    .replace(/\*/g, '•')       // Convert bullets
    .replace(/_{1,2}/g, '')    // Remove italics/underline
    .replace(/`/g, '')         // Remove code ticks
    .trim();
}

function withTimeout<T>(promise: Promise<T>, timeoutMs: number, message: string) {
  return new Promise<T>((resolve, reject) => {
    const timeout = window.setTimeout(() => reject(new Error(message)), timeoutMs);
    promise.then(resolve, reject).finally(() => window.clearTimeout(timeout));
  });
}

export function AIReportButton({ stockData }: AIReportButtonProps) {
  const { t, i18n } = useTranslation();
  const { aiProviderConfig, setAiSettingsOpen } = useUIStore();
  const [loading, setLoading] = useState(false);
  const [report, setReport] = useState('');
  const [toast, setToast] = useState('');
  const reportRef = useRef<HTMLDivElement>(null);
  const currency = currencyForStock(stockData);
  
  const sections = sectionKeys.map((title) => ({
    title,
    content: extractSection(report, title),
  }));

  const showToast = (message: string) => {
    setToast(message);
    window.setTimeout(() => setToast(''), 3500);
  };

  const exportReport = async () => {
    if (!isAIConfigured(aiProviderConfig) && !aiProviderConfig.apiKey) {
      // If not configured, it will fallback to backend, so we check if backend is available or force settings
      // For now, let's allow it if apiKey is missing but provider is auto
      if (aiProviderConfig.provider !== 'auto' && aiProviderConfig.provider !== 'ollama') {
         setAiSettingsOpen(true);
         return;
      }
    }

    const controller = new AbortController();
    setLoading(true);
    setReport('');
    let markdown = '';
    
    try {
      await generateReport(
        aiProviderConfig,
        stockData,
        i18n.language,
        controller.signal,
        (token) => {
          markdown += token;
          setReport(markdown);
        },
      );

      if (!markdown.trim()) {
        throw new Error('AI provider returned an empty report. Please check your settings and try again.');
      }

      // Ensure the UI has updated with the full report before capturing
      flushSync(() => {
        setReport(markdown);
      });

      // Wait for layout to settle and charts to be ready
      await new Promise((resolve) => window.requestAnimationFrame(() => window.requestAnimationFrame(resolve)));
      await new Promise((resolve) => window.setTimeout(resolve, 1000)); // Extra time for charts
      
      if (!reportRef.current) throw new Error('Report render target unavailable');
      
      const canvas = await withTimeout(html2canvas(reportRef.current, {
        backgroundColor: '#ffffff',
        scale: 2, // Higher scale for professional look
        useCORS: true,
        logging: false,
        allowTaint: true,
        windowWidth: 850, // Slightly wider for better layout
      }), 60000, 'Report capture timed out.');

      const image = canvas.toDataURL('image/jpeg', 0.95);
      const pdf = new jsPDF('p', 'mm', 'a4');
      const pageWidth = pdf.internal.pageSize.getWidth();
      const pageHeight = pdf.internal.pageSize.getHeight();
      const imgWidth = pageWidth;
      const imgHeight = (canvas.height * imgWidth) / canvas.width;
      
      let heightLeft = imgHeight;
      let position = 0;

      pdf.addImage(image, 'JPEG', 0, position, imgWidth, imgHeight, undefined, 'FAST');
      heightLeft -= pageHeight;

      while (heightLeft > 0) {
        position = heightLeft - imgHeight;
        pdf.addPage();
        pdf.addImage(image, 'JPEG', 0, position, imgWidth, imgHeight, undefined, 'FAST');
        heightLeft -= pageHeight;
      }

      const date = new Date().toISOString().split('T')[0];
      const filename = `${stockData.profile.ticker}_Research_Report_${date}.pdf`;
      pdf.save(filename);
      showToast(t('aiReportSuccess'));
    } catch (error) {
      console.error('Report generation error:', error);
      showToast(error instanceof Error ? error.message : t('aiError'));
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      <button onClick={exportReport} disabled={loading} className="flex items-center gap-2 rounded-lg bg-slate-700 px-4 py-2 text-white transition-colors hover:bg-slate-600 disabled:opacity-60">
        <FileText className="h-4 w-4" />
        {loading ? t('generatingReport') : t('exportAiReport')}
      </button>
      
      {toast && (
        <div className="fixed bottom-5 left-5 z-[110] rounded-lg bg-slate-800 px-4 py-2 text-sm text-white shadow-xl">
          {toast}
        </div>
      )}

      {/* Hidden Report Template for PDF Capture */}
      <div className="pointer-events-none fixed -left-[9999px] top-0 w-[850px] bg-white p-12 text-slate-900" ref={reportRef}>
        <div className="mb-8 flex items-end justify-between border-b-4 border-slate-900 pb-6">
          <div>
            <h1 className="text-4xl font-black uppercase tracking-tighter text-slate-900">Equity Research Report</h1>
            <p className="text-xl font-bold text-slate-600">{stockData.profile.name || stockData.profile.ticker} ({stockData.profile.ticker})</p>
          </div>
          <div className="text-right">
            <p className="text-sm font-bold uppercase text-slate-500">{new Date().toLocaleDateString(undefined, { dateStyle: 'long' })}</p>
            <p className="text-xs font-black text-red-600 tracking-widest uppercase mt-1">Confidential / AI Generated</p>
          </div>
        </div>

        <div className="mb-10 grid grid-cols-3 gap-6 rounded-xl bg-slate-50 p-6 border border-slate-200">
          <div className="space-y-1">
            <p className="text-[10px] font-black uppercase tracking-widest text-slate-400">Company Overview</p>
            <p className="text-sm"><strong>Sector:</strong> {stockData.profile.sector || 'N/A'}</p>
            <p className="text-sm"><strong>Industry:</strong> {stockData.profile.industry || 'N/A'}</p>
            <p className="text-sm"><strong>Exchange:</strong> {stockData.profile.exchange || 'N/A'}</p>
          </div>
          <div className="space-y-1 border-x border-slate-200 px-6">
            <p className="text-[10px] font-black uppercase tracking-widest text-slate-400">Market Data</p>
            <p className="text-sm"><strong>Price:</strong> {currency} {stockData.profile.current_price?.toLocaleString()}</p>
            <p className="text-sm"><strong>Market Cap:</strong> {stockData.profile.market_cap ? `${currency} ${(stockData.profile.market_cap / 1e9).toFixed(2)}B` : 'N/A'}</p>
            <p className="text-sm"><strong>Currency:</strong> {currency}</p>
          </div>
          <div className="space-y-1 pl-6">
            <p className="text-[10px] font-black uppercase tracking-widest text-slate-400">ML Model Output</p>
            <p className="text-sm"><strong>Predicted:</strong> {currency} {stockData.prediction.predicted_price?.toLocaleString()}</p>
            <p className="text-sm"><strong>Confidence:</strong> {(stockData.prediction.confidence * 100).toFixed(1)}%</p>
            <p className="text-sm"><strong>Trend:</strong> <span className={stockData.prediction.trend === 'increase' ? 'text-emerald-600' : 'text-rose-600'}>{stockData.prediction.trend?.toUpperCase()}</span></p>
          </div>
        </div>

        <div className="space-y-10">
          {sections.map((section) => (
            <section key={section.title} className="break-inside-avoid">
              <h2 className="mb-4 text-lg font-black uppercase tracking-tight text-slate-900 border-l-4 border-slate-900 pl-3 leading-none">
                {section.title}
              </h2>
              <div className="whitespace-pre-wrap text-[13px] leading-relaxed text-slate-700 font-medium">
                {section.content || 'Analysis in progress...'}
              </div>
            </section>
          ))}
        </div>

        <div className="mt-12 border-t border-slate-200 pt-8">
          <p className="text-center text-[10px] font-bold uppercase tracking-widest text-slate-400">
            End of Research Report • Generated by AI Intelligence Dashboard
          </p>
          <p className="mt-4 text-[9px] text-slate-400 text-justify leading-tight italic">
            DISCLAIMER: This report is for informational purposes only and does not constitute financial advice. The analysis is generated using machine learning models and artificial intelligence based on historical data. Investing in securities involves risk. Always consult with a qualified financial advisor before making investment decisions.
          </p>
        </div>
      </div>
    </>
  );
}
