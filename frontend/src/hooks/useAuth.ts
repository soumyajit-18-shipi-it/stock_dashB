import { useAuthStore } from '../store/auth_store';

export function useAuth() {
  const user = useAuthStore((state) => state.user);
  const token = useAuthStore((state) => state.token);
  const loading = useAuthStore((state) => state.loading);
  const error = useAuthStore((state) => state.error);
  const isAdmin = useAuthStore((state) => state.isAdmin);
  const login = useAuthStore((state) => state.login);
  const logout = useAuthStore((state) => state.logout);

  return {
    user,
    token,
    loading,
    error,
    isAdmin,
    login,
    logout,
  };
}
