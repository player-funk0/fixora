import { useState, useCallback } from "react";

// During dev, Vite proxies /api → http://localhost:8000 (see vite.config.js)
// In production, set VITE_API_BASE in .env.production
const API_BASE = import.meta.env.VITE_API_BASE ?? "";

export function useApi() {
  const [token, setTokenState] = useState(
    () => localStorage.getItem("fx_token") ?? null
  );

  const setToken = useCallback((t) => {
    setTokenState(t);
    if (t) localStorage.setItem("fx_token", t);
    else    localStorage.removeItem("fx_token");
  }, []);

  /** Build auth headers — always fresh via closure over `token` state. */
  const authHeaders = useCallback(
    () => (token ? { Authorization: `Bearer ${token}` } : {}),
    [token]
  );

  /** POST with JSON body. Throws plain object on non-2xx. */
  const post = useCallback(
    async (path, body) => {
      const r = await fetch(`${API_BASE}${path}`, {
        method:  "POST",
        headers: { "Content-Type": "application/json", ...authHeaders() },
        body:    JSON.stringify(body),
      });
      const data = await r.json();
      if (!r.ok) throw { status: r.status, ...data };
      return data;
    },
    [authHeaders]
  );

  /** POST with FormData (file upload). No Content-Type header — browser sets boundary. */
  const postForm = useCallback(
    async (path, formData) => {
      const r = await fetch(`${API_BASE}${path}`, {
        method:  "POST",
        headers: authHeaders(),
        body:    formData,
      });
      const data = await r.json();
      if (!r.ok) throw { status: r.status, ...data };
      return data;
    },
    [authHeaders]
  );

  /** GET with optional auth header. */
  const get = useCallback(
    async (path) => {
      const r = await fetch(`${API_BASE}${path}`, {
        headers: { ...authHeaders() },
      });
      const data = await r.json();
      if (!r.ok) throw data;
      return data;
    },
    [authHeaders]
  );

  return { token, setToken, post, postForm, get };
}
