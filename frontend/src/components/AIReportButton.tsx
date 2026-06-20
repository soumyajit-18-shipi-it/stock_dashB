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

function getFallbackContent(title: string, stock: StockResponse, currency: string): string {
  const ticker = stock.profile.ticker;
  const name = stock.profile.name || ticker;
  const sector = stock.profile.sector || 'N/A';
  const industry = stock.profile.industry || 'N/A';
  const exchange = stock.profile.exchange || 'N/A';
  const currentPrice = stock.profile.current_price ? `${currency} ${stock.profile.current_price.toLocaleString()}` : 'N/A';
  const prevClose = stock.profile.previous_close ? `${currency} ${stock.profile.previous_close.toLocaleString()}` : 'N/A';
  const high52 = stock.profile.week_52_high ? `${currency} ${stock.profile.week_52_high.toLocaleString()}` : 'N/A';
  const low52 = stock.profile.week_52_low ? `${currency} ${stock.profile.week_52_low.toLocaleString()}` : 'N/A';
  const predictedPrice = stock.prediction.predicted_price ? `${currency} ${stock.prediction.predicted_price.toLocaleString()}` : 'N/A';
  const trend = stock.prediction.trend || 'stable';
  const confidence = Math.round(stock.prediction.confidence * 100);
  const rmse = stock.metrics.rmse.toFixed(4);
  const mae = stock.metrics.mae.toFixed(4);
  const r2 = stock.metrics.r2.toFixed(4);
  const marketCap = stock.profile.market_cap ? `${currency} ${(stock.profile.market_cap / 1e9).toFixed(2)}B` : 'N/A';

  switch (title) {
    case 'EXECUTIVE SUMMARY':
      return `Based on our comprehensive equity analysis of ${name} (${ticker}), the stock is currently trading at ${currentPrice} and displays a ${trend} trend. The machine learning prediction model forecasts a future price of ${predictedPrice} with a confidence level of ${confidence}%. This outlook integrates historical daily price candles, technical indicators, and sector trends. While the short-term sentiment remains influenced by market factors, the overall technical foundation indicates a stable path forward. Investors should weigh the forecasted trend against macro risks and specific sector dynamics.`;
    
    case 'COMPANY INFORMATION':
      return `${name} (${ticker}) is a leading enterprise operating in the ${sector} sector and ${industry} industry. It is officially listed and traded on the ${exchange} exchange. With a total market capitalization of ${marketCap}, the company maintains a significant footprint in its business domain. Recent corporate developments and market positioning support its current valuation, making it a critical asset to track within the ${industry} space. The company remains focused on driving operational efficiencies and expanding its market reach under prevailing economic conditions.`;
    
    case 'PRICE ANALYSIS':
      return `The current market price of ${ticker} is ${currentPrice}, representing its latest traded value. The security has established a previous close of ${prevClose}, serving as a key benchmark for daily price action. Over the past 52 weeks, the stock has traded within a range defined by a high of ${high52} and a low of ${low52}. This price corridor reflects the historical volatility and support/resistance boundaries for the stock. Current price consolidation near ${currentPrice} will be crucial for determining the next breakout direction.`;
    
    case 'TECHNICAL ANALYSIS':
      return `Our technical analysis of ${ticker} incorporates historical price movements and key mathematical indicators. The recent daily candles demonstrate support around the 52-week low of ${low52} and resistance near the 52-week high of ${high52}. Moving averages (ma7 and ma21) indicate the current trend alignment, while relative strength metrics help identify potential overbought or oversold conditions. The price consolidation at ${currentPrice} suggests that market participants are evaluating the next catalyst for trend resumption or reversal.`;
    
    case 'PREDICTION ANALYSIS':
      return `The machine learning forecasting pipeline has processed the historical data for ${ticker} to generate a prediction. Using the selected model, the predicted price is established at ${predictedPrice}, indicating a ${trend} trend. The model's historical training performance is measured by an RMSE of ${rmse}, MAE of ${mae}, and R-squared coefficient of ${r2}. These metrics define the model's accuracy and reliability. The confidence score of ${confidence}% highlights the statistical likelihood of the projected trend based on historical patterns.`;
    
    case 'BULLISH FACTORS':
      return `• ML Model Outlook: The forecasting model projects a ${trend} price trend towards ${predictedPrice} with a confidence of ${confidence}%.\n• Strong Market Position: As a major player in the ${sector} sector, the company benefits from robust structural demand.\n• Technical Support: The stock's price action shows consistent support near the historical levels, indicating limited downside under current conditions.`;
    
    case 'BEARISH FACTORS':
      return `• Sector Volatility: Operating within the ${industry} industry exposes the stock to systemic market fluctuations and sector rotations.\n• Model Error Margin: The prediction model has a standard error margin (RMSE: ${rmse}, MAE: ${mae}), which could impact short-term forecast precision.\n• Price Resistance: The stock faces strong resistance near its 52-week high of ${high52}, requiring significant volume to break out.`;
    
    case 'RISK ASSESSMENT':
      return `Evaluating the risk profile of ${ticker} requires assessing both systemic market risks and company-specific factors. With a 52-week high of ${high52} and a low of ${low52}, the stock shows a standard trading volatility range. Macroeconomic risks, including interest rate adjustments and inflation, may impact consumer and enterprise spending in the ${sector} sector. Furthermore, reliance on historical patterns for the machine learning model introduces model risk, as black swan events or sudden market regime shifts are not captured by historical price sequences.`;
    
    case 'SCENARIO ANALYSIS':
      return `• Bull Case: If market conditions remain favorable and the stock breaks past immediate resistance, it could target a bullish price ceiling above ${predictedPrice}.\n• Base Case: Under standard market conditions, the stock is expected to align closely with the machine learning model's prediction of ${predictedPrice}.\n• Bear Case: In the event of a broader market correction or sector downturn, the stock may retest its key support level near the 52-week low of ${low52}.`;
    
    case 'RECOMMENDATION':
      return `Based on our quantitative and qualitative evaluation, the recommendation for ${ticker} is to hold the stock, while monitor key support/resistance levels. The machine learning model forecasts a price of ${predictedPrice} with a ${confidence}% confidence level, indicating a ${trend} trend. Long-term investors may consider accumulation near the 52-week low of ${low52}, whereas short-term traders should wait for a confirmed volume breakout above the 52-week high of ${high52} before entering new positions.`;
    
    case 'CONCLUSION':
      return `In conclusion, our equity research report on ${name} (${ticker}) highlights a dynamic outlook. The current price of ${currentPrice} sits within a historical 52-week range of ${low52} to ${high52}. The machine learning model predicts a future price of ${predictedPrice} (${trend} trend) with ${confidence}% confidence. While bullish factors like sector dominance provide support, bearish risks such as macro volatility require careful monitoring. Investors are advised to utilize proper risk-management strategies.`;
    
    default:
      return '';
  }
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
  const [generationComplete, setGenerationComplete] = useState(false);
  const [report, setReport] = useState('');
  const [toast, setToast] = useState('');
  const reportRef = useRef<HTMLDivElement>(null);
  const currency = currencyForStock(stockData);
  
  const sections = sectionKeys.map((title) => {
    let content = extractSection(report, title);
    if (!content && generationComplete) {
      content = getFallbackContent(title, stockData, currency);
    }
    return {
      title,
      content,
    };
  });

  const showToast = (message: string) => {
    setToast(message);
    window.setTimeout(() => setToast(''), 3500);
  };

  const exportReport = async () => {
    if (!isAIConfigured(aiProviderConfig) && !aiProviderConfig.apiKey) {
      if (aiProviderConfig.provider !== 'auto' && aiProviderConfig.provider !== 'ollama') {
         setAiSettingsOpen(true);
         return;
      }
    }

    const controller = new AbortController();
    setLoading(true);
    setGenerationComplete(false);
    setReport('');
    let markdown = '';
    let attempts = 0;
    const maxAttempts = 3;
    let success = false;
    let lastError: Error | null = null;
    
    try {
      while (attempts < maxAttempts && !success) {
        attempts++;
        markdown = '';
        setReport('');
        try {
          console.log(`Attempt ${attempts} of ${maxAttempts}...`);
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
            throw new Error('AI provider returned an empty report.');
          }
          success = true;
        } catch (error) {
          console.warn(`Attempt ${attempts} failed:`, error);
          lastError = error instanceof Error ? error : new Error(String(error));
          if (attempts < maxAttempts) {
            await new Promise((resolve) => window.setTimeout(resolve, 1000 * attempts));
          }
        }
      }

      if (!success && !markdown.trim()) {
        throw lastError || new Error('All attempts failed to generate any report content.');
      }

      if (!success) {
        showToast('Report generation partially completed. Used data-driven fallbacks for missing sections.');
      }

      // Ensure the UI has updated with the full report before capturing
      flushSync(() => {
        setReport(markdown);
        setGenerationComplete(true);
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
                {section.content || (generationComplete ? 'Section generation incomplete. Model token limit reached or generation failed.' : 'Analysis in progress...')}
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
