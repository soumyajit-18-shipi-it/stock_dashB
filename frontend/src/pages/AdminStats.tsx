import { Users, MessageSquare, Calendar, AlertCircle, ArrowLeft, Filter, RefreshCw, ChevronRight } from 'lucide-react';
import { useEffect, useState, useCallback } from 'react';

import { useAuth } from '../hooks/useAuth';
import { api } from '../services/api_client';
import { useUIStore } from '../store/ui_store';

import type { AdminStats as StatsType, FeedbackIssue } from '../types';

export function AdminStats() {
  const { user, token, isAdmin, loading: authLoading } = useAuth();
  const { setCurrentRoute } = useUIStore();

  const [stats, setStats] = useState<StatsType | null>(null);
  const [issues, setIssues] = useState<FeedbackIssue[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Filters
  const [filterStatus, setFilterStatus] = useState<string>('');
  const [filterCategory, setFilterCategory] = useState<string>('');

  const fetchData = useCallback(async () => {
    if (!user || !token || !isAdmin) return;
    setLoading(true);
    setError(null);
    try {
      const [statsData, issuesData] = await Promise.all([
        api.getAdminStats(),
        api.getAdminFeedback(
          filterStatus || undefined,
          filterCategory || undefined
        ),
      ]);
      setStats(statsData);
      setIssues(issuesData);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to fetch admin dashboard statistics.';
      setError(msg);
    } finally {
      setLoading(false);
    }
  }, [user, token, isAdmin, filterStatus, filterCategory]);

  useEffect(() => {
    if (!authLoading && user && token && isAdmin) {
      void fetchData();
    } else if (!authLoading) {
      setLoading(false);
    }
  }, [user, token, isAdmin, authLoading, fetchData]);

  if (authLoading) {
    return (
      <div className="min-h-screen bg-slate-950 flex items-center justify-center">
        <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-emerald-500 mx-auto"></div>
      </div>
    );
  }

  if (!user) {
    return (
      <div className="min-h-screen bg-slate-950 flex items-center justify-center p-4">
        <div className="max-w-md w-full bg-slate-900 border border-slate-800 rounded-2xl p-6 text-center space-y-4">
          <AlertCircle className="h-12 w-12 text-amber-500 mx-auto" />
          <h3 className="text-lg font-bold text-white">Login Required</h3>
          <p className="text-slate-400 text-sm">
            Sign in with Google before opening admin statistics.
          </p>
          <button
            onClick={() => setCurrentRoute('/')}
            className="inline-flex items-center gap-2 px-4 py-2 bg-slate-800 hover:bg-slate-700 text-white rounded-lg text-sm font-semibold transition-colors"
          >
            <ArrowLeft className="h-4 w-4" />
            Back to Dashboard
          </button>
        </div>
      </div>
    );
  }

  if (!isAdmin) {
    return (
      <div className="min-h-screen bg-slate-950 flex items-center justify-center p-4">
        <div className="max-w-md w-full bg-slate-900 border border-slate-800 rounded-2xl p-6 text-center space-y-4">
          <AlertCircle className="h-12 w-12 text-red-500 mx-auto" />
          <h3 className="text-lg font-bold text-white">Access Denied</h3>
          <p className="text-slate-400 text-sm">
            You are not authorized to view this page.
          </p>
          <button
            onClick={() => setCurrentRoute('/')}
            className="inline-flex items-center gap-2 px-4 py-2 bg-slate-800 hover:bg-slate-700 text-white rounded-lg text-sm font-semibold transition-colors"
          >
            <ArrowLeft className="h-4 w-4" />
            Back to Dashboard
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
        
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <button
              onClick={() => setCurrentRoute('/')}
              className="inline-flex items-center gap-1 text-slate-400 hover:text-white text-sm transition-colors mb-2"
            >
              <ArrowLeft className="h-4 w-4" />
              Back to Dashboard
            </button>
            <h1 className="text-3xl font-extrabold text-white tracking-tight">Admin Intelligence Panel</h1>
            <p className="text-slate-400 text-sm mt-1">
              Oversee platform activity, sign-ups, and user-submitted concerns.
            </p>
          </div>
          <button
            onClick={fetchData}
            disabled={loading}
            className="self-start sm:self-center inline-flex items-center gap-2 px-4 py-2 bg-slate-800 hover:bg-slate-700 disabled:opacity-50 text-slate-200 rounded-lg text-sm font-semibold border border-slate-700 transition-colors"
          >
            <RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
            Refresh Data
          </button>
        </div>

        {error && (
          <div className="flex items-start gap-3 p-4 rounded-xl bg-red-500/10 border border-red-500/20 text-red-200">
            <AlertCircle className="h-5 w-5 text-red-400 shrink-0 mt-0.5" />
            <div>
              <h4 className="font-semibold">Failed to fetch data</h4>
              <p className="text-sm text-red-300/90 mt-0.5">{error}</p>
            </div>
          </div>
        )}

        {/* Stats Grid */}
        <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-5 gap-4">
          {/* Total Users */}
          <div className="bg-slate-900 border border-slate-850 rounded-xl p-5 shadow-sm space-y-2 relative overflow-hidden">
            <div className="absolute top-4 right-4 text-emerald-400 bg-emerald-500/10 p-2 rounded-lg">
              <Users className="h-5 w-5" />
            </div>
            <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Total Users</p>
            <h3 className="text-3xl font-bold text-white">{loading ? '...' : stats?.total_users ?? 0}</h3>
            <p className="text-xs text-slate-500">Sign-ups since launch</p>
          </div>

          {/* New Users Today */}
          <div className="bg-slate-900 border border-slate-850 rounded-xl p-5 shadow-sm space-y-2 relative overflow-hidden">
            <div className="absolute top-4 right-4 text-emerald-400 bg-emerald-500/10 p-2 rounded-lg">
              <Calendar className="h-5 w-5" />
            </div>
            <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Today's Signups</p>
            <h3 className="text-3xl font-bold text-white">{loading ? '...' : stats?.new_users_today ?? 0}</h3>
            <p className="text-xs text-emerald-400 font-medium">Active today</p>
          </div>

          {/* New Users This Week */}
          <div className="bg-slate-900 border border-slate-850 rounded-xl p-5 shadow-sm space-y-2 relative overflow-hidden">
            <div className="absolute top-4 right-4 text-emerald-400 bg-emerald-500/10 p-2 rounded-lg">
              <Calendar className="h-5 w-5" />
            </div>
            <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Weekly Signups</p>
            <h3 className="text-3xl font-bold text-white">{loading ? '...' : stats?.new_users_this_week ?? 0}</h3>
            <p className="text-xs text-slate-500">Last 7 days</p>
          </div>

          {/* Total Feedback */}
          <div className="bg-slate-900 border border-slate-850 rounded-xl p-5 shadow-sm space-y-2 relative overflow-hidden">
            <div className="absolute top-4 right-4 text-emerald-400 bg-emerald-500/10 p-2 rounded-lg">
              <MessageSquare className="h-5 w-5" />
            </div>
            <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Total Reports</p>
            <h3 className="text-3xl font-bold text-white">{loading ? '...' : stats?.total_feedback_issues ?? 0}</h3>
            <p className="text-xs text-slate-500">All submissions</p>
          </div>

          {/* Open Feedback */}
          <div className="bg-slate-900 border border-slate-850 rounded-xl p-5 shadow-sm space-y-2 relative overflow-hidden">
            <div className="absolute top-4 right-4 text-emerald-400 bg-emerald-500/10 p-2 rounded-lg">
              <AlertCircle className="h-5 w-5" />
            </div>
            <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Open Reports</p>
            <h3 className="text-3xl font-bold text-white">{loading ? '...' : stats?.open_feedback_issues ?? 0}</h3>
            <p className="text-xs text-slate-400 font-medium">Pending resolution</p>
          </div>
        </div>

        {/* Feedback Listing Section */}
        <div className="bg-slate-900 border border-slate-855 rounded-2xl overflow-hidden shadow-lg">
          <div className="p-6 border-b border-slate-800 flex flex-col md:flex-row md:items-center md:justify-between gap-4">
            <div>
              <h3 className="text-lg font-bold text-white flex items-center gap-2">
                <MessageSquare className="h-5 w-5 text-emerald-400" />
                Submitted Feedback & Issues
              </h3>
              <p className="text-slate-400 text-xs mt-0.5">
                {issues.length} feedback reports found matching parameters.
              </p>
            </div>
            
            {/* Filter controls */}
            <div className="flex flex-wrap items-center gap-3">
              <div className="flex items-center gap-1.5 bg-slate-850 rounded-lg px-2.5 py-1.5 border border-slate-700 text-xs">
                <Filter className="h-3.5 w-3.5 text-slate-400" />
                <span className="text-slate-300 font-medium">Status:</span>
                <select
                  value={filterStatus}
                  onChange={(e) => setFilterStatus(e.target.value)}
                  className="bg-transparent text-white font-semibold focus:outline-none cursor-pointer"
                >
                  <option value="">All Statuses</option>
                  <option value="open">Open</option>
                  <option value="in_review">In Review</option>
                  <option value="planned">Planned</option>
                  <option value="resolved">Resolved</option>
                  <option value="closed">Closed</option>
                </select>
              </div>

              <div className="flex items-center gap-1.5 bg-slate-850 rounded-lg px-2.5 py-1.5 border border-slate-700 text-xs">
                <Filter className="h-3.5 w-3.5 text-slate-400" />
                <span className="text-slate-300 font-medium">Category:</span>
                <select
                  value={filterCategory}
                  onChange={(e) => setFilterCategory(e.target.value)}
                  className="bg-transparent text-white font-semibold focus:outline-none cursor-pointer"
                >
                  <option value="">All Categories</option>
                  <option value="feature_request">Feature Request</option>
                  <option value="bug_report">Bug Report</option>
                  <option value="documentation_issue">Documentation Issue</option>
                  <option value="setup_query">Setup Query</option>
                  <option value="development_query">Development Query</option>
                </select>
              </div>
            </div>
          </div>

          {/* Feedback List */}
          {loading ? (
            <div className="p-12 text-center text-slate-400">
              <div className="animate-spin rounded-full h-6 w-6 border-t-2 border-emerald-500 mx-auto mb-3"></div>
              Loading feedback issues...
            </div>
          ) : issues.length === 0 ? (
            <div className="p-12 text-center text-slate-400 space-y-2">
              <MessageSquare className="h-10 w-10 text-slate-600 mx-auto" />
              <p className="font-semibold">No feedback records found</p>
              <p className="text-xs">Submissions will show up here as users file them.</p>
            </div>
          ) : (
            <div className="divide-y divide-slate-800">
              {issues.map((issue) => (
                <div key={issue.id} className="p-6 hover:bg-slate-850/30 transition-colors space-y-4">
                  <div className="flex flex-wrap items-start justify-between gap-3">
                    <div className="space-y-1">
                      <div className="flex items-center gap-2">
                        <span className="text-xs px-2 py-0.5 rounded-full font-bold bg-slate-800 text-slate-300 uppercase">
                          {issue.category.replace('_', ' ')}
                        </span>
                        <span className={`text-xs px-2 py-0.5 rounded-full font-bold uppercase ${
                          issue.priority === 'urgent' ? 'bg-red-500/20 text-red-400' :
                          issue.priority === 'high' ? 'bg-orange-500/20 text-orange-400' :
                          issue.priority === 'low' ? 'bg-slate-800 text-slate-400' :
                          'bg-slate-800 text-slate-300'
                        }`}>
                          {issue.priority} priority
                        </span>
                      </div>
                      <h4 className="text-base font-bold text-white">{issue.title}</h4>
                      <p className="text-xs text-slate-400">
                        Submitted by: <span className="text-slate-200">{issue.email || 'Anonymous'}</span> on {new Date(issue.created_at).toLocaleString()}
                      </p>
                    </div>

                    <span className={`text-xs px-3 py-1 rounded-lg font-bold border ${
                      issue.status === 'open' ? 'border-emerald-500/30 bg-emerald-500/10 text-emerald-400' :
                      issue.status === 'in_review' ? 'border-amber-500/30 bg-amber-500/10 text-amber-400' :
                      issue.status === 'resolved' ? 'border-slate-700 bg-slate-800 text-slate-300' :
                      'border-slate-800 bg-slate-950 text-slate-500'
                    }`}>
                      {issue.status.toUpperCase()}
                    </span>
                  </div>

                  <p className="text-sm text-slate-300 whitespace-pre-wrap">{issue.description}</p>

                  <div className="flex flex-wrap items-center gap-x-6 gap-y-2 pt-2 text-xs text-slate-400 border-t border-slate-800/60">
                    {issue.page_url && (
                      <span className="truncate max-w-sm">
                        Captured URL:{' '}
                        <a
                          href={issue.page_url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-emerald-400 hover:underline inline-flex items-center gap-0.5"
                        >
                          {issue.page_url}
                          <ChevronRight className="h-3 w-3" />
                        </a>
                      </span>
                    )}
                    {issue.screenshot_url && (
                      <span>
                        Link/Screenshot:{' '}
                        <a
                          href={issue.screenshot_url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-emerald-400 hover:underline inline-flex items-center gap-0.5"
                        >
                          View Attachment
                          <ChevronRight className="h-3 w-3" />
                        </a>
                      </span>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
export default AdminStats;
