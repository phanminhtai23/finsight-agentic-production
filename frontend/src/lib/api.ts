import axios from "axios";
import type { StreamEvent } from "./types";

// In dev this is "/api/v1" (proxied by Vite to the backend). In production (e.g. Vercel)
// set VITE_API_BASE_URL to your deployed backend, e.g. "https://api.example.com/api/v1".
export const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "/api/v1";

const ACCESS = "finsight_access";
const REFRESH = "finsight_refresh";

export const tokens = {
  get access() {
    return localStorage.getItem(ACCESS);
  },
  get refresh() {
    return localStorage.getItem(REFRESH);
  },
  set(access: string, refresh?: string) {
    localStorage.setItem(ACCESS, access);
    if (refresh) localStorage.setItem(REFRESH, refresh);
  },
  clear() {
    localStorage.removeItem(ACCESS);
    localStorage.removeItem(REFRESH);
  },
};

export const api = axios.create({ baseURL: API_BASE });

api.interceptors.request.use((config) => {
  const access = tokens.access;
  if (access) config.headers.Authorization = `Bearer ${access}`;
  return config;
});

let refreshing: Promise<string | null> | null = null;

async function doRefresh(): Promise<string | null> {
  const refresh = tokens.refresh;
  if (!refresh) return null;
  try {
    const res = await axios.post(`${API_BASE}/auth/refresh`, { refresh_token: refresh });
    tokens.set(res.data.access_token);
    return res.data.access_token as string;
  } catch {
    tokens.clear();
    return null;
  }
}

api.interceptors.response.use(
  (res) => res,
  async (error) => {
    const config = error.config;
    if (error.response?.status === 401 && config && !config._retry) {
      config._retry = true;
      refreshing = refreshing ?? doRefresh();
      const access = await refreshing;
      refreshing = null;
      if (access) {
        config.headers.Authorization = `Bearer ${access}`;
        return api(config);
      }
    }
    return Promise.reject(error);
  },
);

/** Stream a chat answer over SSE (fetch, since axios doesn't stream in the browser). */
export async function streamChat(
  conversationId: string,
  message: string,
  thinking: boolean,
  onEvent: (ev: StreamEvent) => void,
  signal?: AbortSignal,
): Promise<void> {
  const res = await fetch(`${API_BASE}/conversations/${conversationId}/messages/stream`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${tokens.access ?? ""}`,
    },
    body: JSON.stringify({ message, thinking }),
    signal,
  });
  if (!res.ok || !res.body) throw new Error(`Stream failed (${res.status})`);

  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  for (;;) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    const chunks = buffer.split("\n\n");
    buffer = chunks.pop() ?? "";
    for (const chunk of chunks) {
      const dataLine = chunk.split("\n").find((l) => l.startsWith("data:"));
      if (!dataLine) continue;
      try {
        onEvent(JSON.parse(dataLine.slice(5).trim()) as StreamEvent);
      } catch {
        /* ignore malformed event */
      }
    }
  }
}

export function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / 1024 / 1024).toFixed(1)} MB`;
}
