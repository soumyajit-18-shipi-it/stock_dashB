import { useAuth } from '../hooks/useAuth';

export function AuthButton() {
  const { login, loading } = useAuth();

  return (
    <button
      onClick={login}
      disabled={loading}
      className="inline-flex items-center gap-2 px-4 py-2 bg-slate-800 hover:bg-slate-700 text-white border border-slate-700 rounded-lg text-sm font-semibold shadow transition-colors duration-200 disabled:opacity-50 disabled:cursor-not-allowed"
    >
      <svg className="h-4 w-4" viewBox="0 0 24 24" width="24" height="24" xmlns="http://www.w3.org/2000/svg">
        <g transform="matrix(1, 0, 0, 1, 0, 0)">
          <path d="M21.35,11.1H12v2.7h5.38c-0.24,1.28 -0.96,2.37 -2.04,3.1v2.58h3.3c1.93,-1.78 3.04,-4.4 3.04,-7.48C21.68,11.83 21.56,11.4 21.35,11.1z" fill="#4285F4" />
          <path d="M12,20.6c2.43,0 4.47,-0.8 5.96,-2.2l-3.3,-2.58c-0.92,0.62 -2.1,0.98 -3.3,0.98 -2.35,0 -4.34,-1.58 -5.05,-3.72H2.9v2.66C4.38,18.7 8.0,20.6 12,20.6z" fill="#34A853" />
          <path d="M6.95,13.08c-0.18,-0.54 -0.28,-1.11 -0.28,-1.7s0.1,-1.16 0.28,-1.7V7.02H2.9C2.3,8.22 2,9.57 2,11s0.3,2.78 0.9,3.98l4.05,-2.9z" fill="#FBBC05" />
          <path d="M12,5.62c1.32,0 2.5,0.45 3.44,1.35l2.58,-2.58C16.46,2.9 14.42,2.2 12,2.2c-4.0,0 -7.62,1.9 -9.1,4.82l4.05,2.9C7.66,7.2 9.65,5.62 12,5.62z" fill="#EA4335" />
        </g>
      </svg>
      {loading ? 'Connecting...' : 'Continue with Google'}
    </button>
  );
}
export default AuthButton;
