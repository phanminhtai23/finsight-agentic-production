import { createContext, useContext, useEffect, useState, type ReactNode } from "react";
import { api, tokens } from "../lib/api";
import type { User } from "../lib/types";

interface AuthState {
  user: User | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  loginWithGoogle: (idToken: string) => Promise<void>;
  logout: () => void;
  refreshUser: () => Promise<void>;
  setUser: (user: User) => void;
}

const AuthContext = createContext<AuthState>({
  user: null,
  loading: true,
  login: async () => {},
  loginWithGoogle: async () => {},
  logout: () => {},
  refreshUser: async () => {},
  setUser: () => {},
});

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  async function refreshUser() {
    try {
      const { data } = await api.get<User>("/auth/me");
      setUser(data);
    } catch {
      setUser(null);
    }
  }

  useEffect(() => {
    (async () => {
      if (tokens.access) await refreshUser();
      setLoading(false);
    })();
  }, []);

  async function login(email: string, password: string) {
    const { data } = await api.post("/auth/login", { email, password });
    tokens.set(data.access_token, data.refresh_token);
    await refreshUser();
  }

  async function loginWithGoogle(idToken: string) {
    const { data } = await api.post("/auth/google", { id_token: idToken });
    tokens.set(data.access_token, data.refresh_token);
    await refreshUser();
  }

  function logout() {
    tokens.clear();
    setUser(null);
  }

  return (
    <AuthContext.Provider
      value={{ user, loading, login, loginWithGoogle, logout, refreshUser, setUser }}
    >
      {children}
    </AuthContext.Provider>
  );
}

// eslint-disable-next-line react-refresh/only-export-components
export const useAuth = () => useContext(AuthContext);
