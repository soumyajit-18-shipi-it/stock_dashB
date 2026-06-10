import { AlertCircle, RefreshCw } from 'lucide-react';

interface ErrorMessageProps {
  message: string;
  onRetry?: () => void;
}

export function ErrorMessage({ message, onRetry }: ErrorMessageProps) {
  return (
    <div className="bg-red-500/10 border border-red-500/30 rounded-xl p-6 text-center">
      <AlertCircle className="h-12 w-12 text-red-400 mx-auto mb-4" />
      <h3 className="text-lg font-semibold text-white mb-2">Error Loading Data</h3>
      <p className="text-slate-400 mb-4">{message}</p>
      {onRetry && (
        <button
          onClick={onRetry}
          className="inline-flex items-center gap-2 px-4 py-2 bg-slate-700 hover:bg-slate-600 text-white rounded-lg transition-colors"
        >
          <RefreshCw className="h-4 w-4" />
          Retry
        </button>
      )}
    </div>
  );
}

export function EmptyState() {
  return (
    <div className="bg-slate-800/30 border border-slate-700 rounded-xl p-12 text-center">
      <div className="w-16 h-16 bg-slate-700 rounded-full flex items-center justify-center mx-auto mb-4">
        <TrendingUpIcon className="h-8 w-8 text-slate-400" />
      </div>
      <h3 className="text-lg font-semibold text-white mb-2">No Stock Selected</h3>
      <p className="text-slate-400">Search for a ticker symbol to view stock analysis and predictions.</p>
    </div>
  );
}

function TrendingUpIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
    </svg>
  );
}
