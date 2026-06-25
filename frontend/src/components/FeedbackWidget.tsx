import { MessageSquare, X, CheckCircle, AlertCircle } from 'lucide-react';
import { useState, useEffect, type FormEvent } from 'react';

import { useAuth } from '../hooks/useAuth';
import { api } from '../services/api_client';

export function FeedbackWidget() {
  const [isOpen, setIsOpen] = useState(false);
  const { user, login } = useAuth();
  
  const [category, setCategory] = useState('bug_report');
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [screenshotUrl, setScreenshotUrl] = useState('');
  const [pageUrl, setPageUrl] = useState('');

  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (isOpen) {
      setPageUrl(window.location.href);
      setSuccess(false);
      setError(null);
    }
  }, [isOpen]);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    if (!user) return;
    
    setLoading(true);
    setError(null);
    try {
      await api.submitFeedback(category, title, description, pageUrl, screenshotUrl || undefined);
      setSuccess(true);
      setTitle('');
      setDescription('');
      setScreenshotUrl('');
      setTimeout(() => {
        setIsOpen(false);
        setSuccess(false);
      }, 3000);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'An error occurred while submitting feedback.';
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        setIsOpen(false);
      }
    };
    if (isOpen) {
      window.addEventListener('keydown', handleKeyDown);
    }
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen]);

  return (
    <>
      <button
        onClick={() => setIsOpen(true)}
        className="fixed bottom-20 right-5 z-40 flex items-center gap-1.5 px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white border border-slate-700 rounded-lg text-xs font-semibold shadow-lg shadow-black/25 hover:scale-105 active:scale-95 transition-all duration-200"
        aria-label="Report Issue or Request Feature"
      >
        <MessageSquare className="h-3.5 w-3.5" />
        <span>Report Issue</span>
      </button>

      {isOpen && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/60 backdrop-blur-sm"
          role="dialog"
          aria-modal="true"
          aria-labelledby="feedback-title"
        >
          <div className="relative w-full max-w-lg bg-slate-900 border border-slate-800 rounded-2xl shadow-2xl p-6 overflow-hidden max-h-[90vh] flex flex-col">
            
            <div className="flex items-center justify-between pb-4 border-b border-slate-800">
              <h2 id="feedback-title" className="text-lg font-bold text-white">
                Submit Feedback / Issues
              </h2>
              <button
                onClick={() => setIsOpen(false)}
                className="p-1 hover:bg-slate-800 rounded-lg text-slate-400 hover:text-white transition-colors"
                aria-label="Close modal"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            <div className="flex-1 overflow-y-auto pt-4 space-y-4">
              {!user ? (
                <div className="text-center py-8 space-y-4">
                  <p className="text-slate-300">
                    Please continue with Google to submit feedback.
                  </p>
                  <button
                    onClick={login}
                    className="inline-flex items-center gap-2 px-6 py-2.5 bg-slate-800 hover:bg-slate-700 text-white border border-slate-700 rounded-lg font-semibold shadow transition-colors"
                  >
                    Continue with Google
                  </button>
                </div>
              ) : success ? (
                <div className="text-center py-8 space-y-3">
                  <CheckCircle className="h-12 w-12 text-emerald-400 mx-auto animate-bounce" />
                  <h3 className="text-lg font-semibold text-white">Submitted!</h3>
                  <p className="text-slate-400 text-sm">
                    Thanks! Your issue has been submitted.
                  </p>
                </div>
              ) : (
                <form onSubmit={handleSubmit} className="space-y-4">
                  
                  {error && (
                    <div className="flex items-start gap-2.5 p-3 rounded-lg bg-red-500/10 border border-red-500/20 text-red-200 text-sm">
                      <AlertCircle className="h-5 w-5 text-red-400 shrink-0 mt-0.5" />
                      <span>{error}</span>
                    </div>
                  )}

                  <div>
                    <label htmlFor="category" className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-1.5">
                      Category
                    </label>
                    <select
                      id="category"
                      value={category}
                      onChange={(e) => setCategory(e.target.value)}
                      className="w-full rounded-lg border border-slate-700 bg-slate-800 text-slate-200 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent"
                      required
                    >
                      <option value="feature_request">Feature Request</option>
                      <option value="bug_report">Bug Report</option>
                      <option value="documentation_issue">Documentation Issue</option>
                      <option value="setup_query">Setup Query</option>
                      <option value="development_query">Development Query</option>
                    </select>
                  </div>

                  <div>
                    <label htmlFor="email" className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-1.5">
                      Your Email
                    </label>
                    <input
                      type="email"
                      id="email"
                      value={user.email || ''}
                      readOnly
                      disabled
                      className="w-full rounded-lg border border-slate-800 bg-slate-950 text-slate-500 px-3 py-2 text-sm cursor-not-allowed"
                    />
                  </div>

                  <div>
                    <label htmlFor="title" className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-1.5">
                      Title
                    </label>
                    <input
                      type="text"
                      id="title"
                      value={title}
                      onChange={(e) => setTitle(e.target.value)}
                      placeholder="Brief summary of the issue or request"
                      className="w-full rounded-lg border border-slate-700 bg-slate-800 text-slate-200 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent"
                      required
                    />
                  </div>

                  <div>
                    <label htmlFor="description" className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-1.5">
                      Description
                    </label>
                    <textarea
                      id="description"
                      value={description}
                      onChange={(e) => setDescription(e.target.value)}
                      placeholder="Provide details about the issue or feature request"
                      rows={4}
                      className="w-full rounded-lg border border-slate-700 bg-slate-800 text-slate-200 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent"
                      required
                    />
                  </div>

                  <div>
                    <label htmlFor="pageUrl" className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-1.5">
                      Page URL (Auto-captured)
                    </label>
                    <input
                      type="text"
                      id="pageUrl"
                      value={pageUrl}
                      readOnly
                      disabled
                      className="w-full rounded-lg border border-slate-800 bg-slate-950 text-slate-500 px-3 py-2 text-sm cursor-not-allowed"
                    />
                  </div>

                  <div>
                    <label htmlFor="screenshot" className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-1.5">
                      Screenshot or Link (Optional)
                    </label>
                    <input
                      type="url"
                      id="screenshot"
                      value={screenshotUrl}
                      onChange={(e) => setScreenshotUrl(e.target.value)}
                      placeholder="https://example.com/screenshot.png"
                      className="w-full rounded-lg border border-slate-700 bg-slate-800 text-slate-200 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent"
                    />
                  </div>

                  <div className="pt-2">
                    <button
                      type="submit"
                      disabled={loading}
                      className="w-full py-2.5 bg-emerald-500 hover:bg-emerald-600 active:bg-emerald-700 text-white font-semibold rounded-lg shadow-lg hover:shadow-emerald-500/20 transition-all duration-150 disabled:opacity-50"
                    >
                      {loading ? 'Submitting...' : 'Submit Feedback'}
                    </button>
                  </div>
                </form>
              )}
            </div>
          </div>
        </div>
      )}
    </>
  );
}
export default FeedbackWidget;
