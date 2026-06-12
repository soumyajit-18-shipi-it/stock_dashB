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
  'reportPriceAnalysis',
  'reportPrediction',
  'reportTechnicalOverview',
  'reportRisks',
  'reportRecommendation',
] as const;

function extractSection(text: string, title: string, allTitles: string[]) {
  const escaped = title.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  const nextTitles = allTitles.filter((item) => item !== title).map((item) => item.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')).join('|');
  const pattern = nextTitles
    ? new RegExp(`(?:^|\\n)\\s*(?:#+\\s*)?${escaped}\\s*:?\\s*\\n?([\\s\\S]*?)(?=\\n\\s*(?:#+\\s*)?(?:${nextTitles})\\s*:?\\s*\\n|$)`, 'i')
    : null;
  const match = pattern?.exec(text);
  return match?.[1]?.trim() || '';
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
  const sectionTitles = sectionKeys.map((key) => t(key));
  const sections = sectionKeys.map((key, index) => ({
    key,
    title: sectionTitles[index],
    content: extractSection(report, sectionTitles[index], sectionTitles) || (index === 2 ? report : ''),
  }));

  const showToast = (message: string) => {
    setToast(message);
    window.setTimeout(() => setToast(''), 3500);
  };

  const exportReport = async () => {
    if (!isAIConfigured(aiProviderConfig)) {
      setAiSettingsOpen(true);
      return;
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

      // Wait for two animation frames to ensure layout is stable
      await new Promise((resolve) => window.requestAnimationFrame(() => window.requestAnimationFrame(resolve)));
      
      if (!reportRef.current) throw new Error('Report render target unavailable');
      
      // Check if element is actually renderable
      const rect = reportRef.current.getBoundingClientRect();
      if (rect.width === 0 || reportRef.current.scrollHeight === 0) {
        throw new Error('Report content is not visible or empty');
      }

      const canvas = await withTimeout(html2canvas(reportRef.current, {
        backgroundColor: '#ffffff',
        scale: 1.5, // Lower scale for speed
        useCORS: true,
        logging: false,
        allowTaint: true,
        windowWidth: 794, // Fixed A4 width in px at 96 DPI
      }), 45000, 'Report capture timed out. The report might be too long.');

      if (!canvas || canvas.width === 0 || canvas.height === 0) {
        throw new Error('Report capture failed to produce a valid image.');
      }

      const image = canvas.toDataURL('image/png', 1.0);
      if (!image || image === 'data:,') throw new Error('Report capture produced a blank image');

      const pdf = new jsPDF('p', 'mm', 'a4');
      const pageWidth = pdf.internal.pageSize.getWidth();
      const pageHeight = pdf.internal.pageSize.getHeight();
      const imgWidth = pageWidth;
      const imgHeight = (canvas.height * imgWidth) / canvas.width;
      
      let heightLeft = imgHeight;
      let position = 0;

      // Add first page
      pdf.addImage(image, 'PNG', 0, position, imgWidth, imgHeight, undefined, 'FAST');
      heightLeft -= pageHeight;

      // Add subsequent pages if necessary
      while (heightLeft > 0) {
        position = heightLeft - imgHeight;
        pdf.addPage();
        pdf.addImage(image, 'PNG', 0, position, imgWidth, imgHeight, undefined, 'FAST');
        heightLeft -= pageHeight;
      }

      const date = new Date().toISOString().split('T')[0];
      const filename = `${stockData.profile.ticker}_AI_Report_${date}.pdf`;
      pdf.save(filename);
      showToast(t('aiReportSuccess'));
    } catch (error) {
      console.error('Report generation error:', error);
      const message = error instanceof Error ? error.message : t('aiError');
      showToast(message);
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
      <div className="pointer-events-none fixed -left-[9999px] top-0 w-[794px] bg-white p-10 text-slate-950" ref={reportRef}>
        <div className="mb-6 flex items-start justify-between border-b border-slate-300 pb-4">
          <div>
            <h1 className="text-3xl font-bold">{t('reportTitle', { ticker: stockData.profile.ticker })}</h1>
            <p className="text-sm text-slate-600">{stockData.profile.name || stockData.profile.ticker}</p>
          </div>
          <p className="text-sm font-semibold text-red-700">{t('aiDisclaimerWatermark')}</p>
        </div>
        <div className="mb-6 grid grid-cols-2 gap-3 rounded-lg border border-slate-200 bg-slate-50 p-4 text-sm">
          <p><strong>{t('reportCompany')}:</strong> {stockData.profile.name || stockData.profile.ticker}</p>
          <p><strong>{t('reportExchange')}:</strong> {stockData.profile.exchange || t('notAvailable')}</p>
          <p><strong>{t('reportCurrency')}:</strong> {currency}</p>
          <p><strong>{t('reportModelUsed')}:</strong> {stockData.prediction.model_used === 'rf' ? t('randomForest') : t('linear')}</p>
          <p><strong>{t('reportDate')}:</strong> {new Date().toLocaleDateString()}</p>
          <p><strong>{t('currentPrice')}:</strong> {stockData.profile.current_price ?? t('notAvailable')}</p>
        </div>
        <div className="space-y-6 text-sm leading-6">
          {sections.map((section) => (
            <section key={section.key}>
              <h2 className="mb-2 text-xl font-bold text-slate-950">{section.title}</h2>
              <div className="whitespace-pre-wrap text-slate-800">{section.content || t('notAvailable')}</div>
            </section>
          ))}
        </div>
        <p className="mt-8 border-t border-slate-300 pt-4 text-xs font-semibold uppercase tracking-wide text-slate-500">{t('aiDisclaimerWatermark')}</p>
      </div>
    </>
  );
}
