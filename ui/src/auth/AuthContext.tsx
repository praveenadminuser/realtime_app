// Holds auth state for the whole app: who's logged in, and login/logout actions.
// One provider near the root, consumed anywhere via useAuth(). This is what lets the
// router gate protected pages and the dashboard show the current user.
import { createContext, useEffect, useState, type ReactNode } from "react";

import * as authApi from "../api/auth";
import type { UserRead } from "../types/user";
import { clearToken, getToken, setToken } from "./storage";

// "loading" matters: on first paint we don't yet know if the stored token is valid, so
// ProtectedRoute must wait rather than flash the login page.
type Status = "loading" | "authenticated" | "anonymous";

interface AuthValue {
  user: UserRead | null;
  status: Status;
  login: (username: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
}

// null! — the provider always wraps the tree, so consumers get a real value.
export const AuthContext = createContext<AuthValue>(null!);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<UserRead | null>(null);
  const [status, setStatus] = useState<Status>("loading");

  // On load: if a token is stored, validate it by fetching the user. A stale/expired
  // token 401s (client.ts clears it) and we land as anonymous. No token → anonymous.
  useEffect(() => {
    if (!getToken()) {
      setStatus("anonymous");
      return;
    }
    authApi
      .getMe()
      .then((u) => {
        setUser(u);
        setStatus("authenticated");
      })
      .catch(() => {
        clearToken();
        setStatus("anonymous");
      });
  }, []);

  async function login(username: string, password: string) {
    const token = await authApi.login(username, password); // throws ApiError on bad creds
    setToken(token.access_token);
    setUser(await authApi.getMe());
    setStatus("authenticated");
  }

  async function logout() {
    // Best-effort server call; even if it fails (already-expired token), we still drop
    // the local token — THAT is the real logout for a stateless JWT.
    try {
      await authApi.logout();
    } catch {
      /* ignore */
    }
    clearToken();
    setUser(null);
    setStatus("anonymous");
  }

  return (
    <AuthContext.Provider value={{ user, status, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}