import { createContext, useContext, useMemo, useState } from "react";
import * as api from "./api";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [token, setTokenState] = useState(api.getToken());

  const value = useMemo(
    () => ({
      isAuthenticated: Boolean(token),
      async login(email, password) {
        const data = await api.login(email, password);
        setTokenState(data.access_token);
      },
      async register(email, password) {
        await api.register(email, password);
      },
      logout() {
        api.clearToken();
        setTokenState(null);
      },
    }),
    [token]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
