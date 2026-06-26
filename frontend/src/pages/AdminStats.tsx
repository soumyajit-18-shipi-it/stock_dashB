import { Users, MessageSquare, Calendar, AlertCircle, ArrowLeft, Filter, RefreshCw, ChevronRight, Activity, UserPlus, Search } from 'lucide-react';
import { useEffect, useState, useCallback } from 'react';

import { useAuth } from '../hooks/useAuth';
import { api } from '../services/api_client';
import { useUIStore } from '../store/ui_store';

import type { AdminStats as StatsType, FeedbackIssue, AdminUserSummary } from '../types';

function formatDate(value?: string) {
  if (!value) return 'Not recorded';
  return new Date(value).toLocaleString();
}

function userDisplayName(user?: Pick<AdminUserSummary, 'full_name' | 'email'>) {
  return user?.full_name?.trim() || 'Unknown User';
}

function initials(name?: string, email?: string) {
  const source = name?.trim() || email || '?';
  return source.slice(0, 2).toUpperCase();
}

function Avatar({ user, size = 'md' }: { user: Pick<AdminUserSummary, 'full_name' | 'email' | 'avatar_url'>; size?: 'sm' | 'md' }) {
  const className = size === 'sm' ? 'h-8 w-8 text-xs' : 'h-10 w-10 text-sm';
  if (user.avatar_url) {
    return (
      <img
        src={user.avatar_url}
        alt=""
        className={`${className} rounded-full bg-slate-800 object-cover border border-slate-700`}
        referrerPolicy="no-referrer"
      />
    );
  }
  return (
    <div className={`${className} rounded-full bg-emerald-500/15 text-emerald-300 border border-emerald-500/20 flex items-center justify-center font-bold`}>
      {initials(user.full_name, user.email)}
    </div>
  );
}

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
  const [filterUser, setFilterUser] = useState<string>('');

  const visibleIssues = issues.filter((issue) => {
    const needle = filterUser.trim().toLowerCase();
    if (!needle) return true;
    return [issue.email, issue.submitter_name, issue.title]
      .filter(Boolean)
      .some((value) => String(value).toLowerCase().includes(needle));
  });

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
      const raw = err instanceof Error ? err.message : 'Failed to fetch admin dashboard statistics.';
      const friendly = raw.toLowerCase().includes('token')
        ? 'Your admin session could not be verified. Please sign out, sign back in with an allowlisted admin email, and refresh.'
        : raw;
      setError(friendly);
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
        <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-6 gap-4">
          {/* Total Users */}
          <div className="bg-slate-900 border border-slate-850 rounded-xl p-5 shadow-sm space-y-2 relative overflow-hidden">
            <div className="absolute top-4 right-4 text-emerald-400 bg-emerald-500/10 p-2 rounded-lg">
              <Users className="h-5 w-5" />
            </div>
            <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Total Users</p>
            <h3 className="text-3xl font-bold text-white">{loading ? '...' : stats?.total_users ?? 0}</h3>
            <p className="text-xs text-slate-500">Sign-ups since launch</p>
          </div>

          {/* Active Today */}
          <div className="bg-slate-900 border border-slate-850 rounded-xl p-5 shadow-sm space-y-2 relative overflow-hidden">
            <div className="absolute top-4 right-4 text-emerald-400 bg-emerald-500/10 p-2 rounded-lg">
              <Activity className="h-5 w-5" />
            </div>
            <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Active Today</p>
            <h3 className="text-3xl font-bold text-white">{loading ? '...' : stats?.active_today ?? 0}</h3>
            <p className="text-xs text-slate-500">Seen in last 24h</p>
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

        {/* User Analytics */}
        <section className="space-y-4">
          <div>
            <h2 className="text-xl font-bold text-white">User Analytics</h2>
            <p className="text-slate-400 text-sm">Recent signups and authenticated user activity.</p>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden">
              <div className="p-4 border-b border-slate-800 flex items-center gap-2">
                <UserPlus className="h-5 w-5 text-emerald-400" />
                <h3 className="font-bold text-white">Latest Signups</h3>
              </div>
              <div className="divide-y divide-slate-800">
                {loading ? (
                  <div className="p-6 text-sm text-slate-400">Loading signups...</div>
                ) : (stats?.latest_signups?.length ?? 0) === 0 ? (
                  <div className="p-6 text-sm text-slate-400">No user profiles found. Run the Supabase backfill SQL if users already signed in.</div>
                ) : (
                  stats?.latest_signups.map((signup) => (
                    <div key={signup.id} className="p-4 flex items-center gap-3">
                      <Avatar user={signup} />
                      <div className="min-w-0 flex-1">
                        <p className="font-semibold text-white truncate">{userDisplayName(signup)}</p>
                        <p className="text-xs text-slate-400 truncate">{signup.email || 'No email recorded'}</p>
                        <p className="text-xs text-slate-500 mt-1">First seen {formatDate(signup.first_seen_at)}</p>
                      </div>
                      <span className="text-xs px-2 py-1 rounded-md bg-slate-800 text-slate-300 uppercase">
                        {signup.provider || 'unknown'}
                      </span>
                    </div>
                  ))
                )}
              </div>
            </div>

            <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden">
              <div className="p-4 border-b border-slate-800 flex items-center gap-2">
                <Users className="h-5 w-5 text-emerald-400" />
                <h3 className="font-bold text-white">Recent Users</h3>
              </div>
              <div className="overflow-x-auto">
                <table className="min-w-full text-sm">
                  <thead className="bg-slate-950/60 text-slate-400 text-xs uppercase">
                    <tr>
                      <th className="text-left font-semibold p-3">User</th>
                      <th className="text-left font-semibold p-3">Last Seen</th>
                      <th className="text-right font-semibold p-3">Activity</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800">
                    {loading ? (
                      <tr><td colSpan={3} className="p-6 text-slate-400">Loading users...</td></tr>
                    ) : (stats?.users?.length ?? 0) === 0 ? (
                      <tr><td colSpan={3} className="p-6 text-slate-400">No users found.</td></tr>
                    ) : (
                      stats?.users.map((appUser) => (
                        <tr key={appUser.id} className="hover:bg-slate-850/30">
                          <td className="p-3">
                            <div className="flex items-center gap-3 min-w-64">
                              <Avatar user={appUser} size="sm" />
                              <div className="min-w-0">
                                <p className="font-semibold text-white truncate">{userDisplayName(appUser)}</p>
                                <p className="text-xs text-slate-400 truncate">{appUser.email || 'No email recorded'}</p>
                              </div>
                            </div>
                          </td>
                          <td className="p-3 text-slate-300 whitespace-nowrap">{formatDate(appUser.last_seen_at)}</td>
                          <td className="p-3 text-right text-slate-300 whitespace-nowrap">
                            <span title="Feedback reports">{appUser.total_feedback_count ?? 0} reports</span>
                            <span className="text-slate-600 mx-1">/</span>
                            <span title="Watchlist items">{appUser.total_watchlist_items ?? 0} watchlist</span>
                            <span className="text-slate-600 mx-1">/</span>
                            <span title="Searches">{appUser.total_searches ?? 0} searches</span>
                          </td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        </section>

        {/* Feedback Listing Section */}
        <div className="bg-slate-900 border border-slate-855 rounded-2xl overflow-hidden shadow-lg">
          <div className="p-6 border-b border-slate-800 flex flex-col md:flex-row md:items-center md:justify-between gap-4">
            <div>
              <h3 className="text-lg font-bold text-white flex items-center gap-2">
                <MessageSquare className="h-5 w-5 text-emerald-400" />
                Submitted Feedback & Issues
              </h3>
              <p className="text-slate-400 text-xs mt-0.5">
                {visibleIssues.length} feedback reports found matching parameters.
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

              <label className="flex items-center gap-1.5 bg-slate-850 rounded-lg px-2.5 py-1.5 border border-slate-700 text-xs">
                <Search className="h-3.5 w-3.5 text-slate-400" />
                <span className="text-slate-300 font-medium">User:</span>
                <input
                  value={filterUser}
                  onChange={(e) => setFilterUser(e.target.value)}
                  placeholder="Name or email"
                  className="bg-transparent text-white placeholder:text-slate-500 focus:outline-none w-32"
                />
              </label>
            </div>
          </div>

          {/* Feedback List */}
          {loading ? (
            <div className="p-12 text-center text-slate-400">
              <div className="animate-spin rounded-full h-6 w-6 border-t-2 border-emerald-500 mx-auto mb-3"></div>
              Loading feedback issues...
            </div>
          ) : visibleIssues.length === 0 ? (
            <div className="p-12 text-center text-slate-400 space-y-2">
              <MessageSquare className="h-10 w-10 text-slate-600 mx-auto" />
              <p className="font-semibold">No feedback records found</p>
              <p className="text-xs">Submissions will show up here as users file them.</p>
            </div>
          ) : (
            <div className="divide-y divide-slate-800">
              {visibleIssues.map((issue) => (
                <div key={issue.id} className="p-6 hover:bg-slate-850/30 transition-colors space-y-4">
                  <div className="flex flex-wrap items-start justify-between gap-3">
                    <div className="space-y-2 min-w-0">
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
                      <div className="flex items-center gap-2 text-xs text-slate-400">
                        <Avatar
                          user={{
                            full_name: issue.submitter_name,
                            email: issue.email,
                            avatar_url: issue.submitter_avatar_url,
                          }}
                          size="sm"
                        />
                        <p className="min-w-0">
                          Submitted by:{' '}
                          <span className="text-slate-200">
                            {issue.submitter_name || 'Unknown User'} ({issue.email || 'no email recorded'})
                          </span>
                          {' '}on {formatDate(issue.created_at)}
                        </p>
                      </div>
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
