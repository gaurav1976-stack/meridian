// Minimal typed fetch wrapper. In production this would also attach bearer
// tokens; in dev the FastAPI `allow_dev_auth_bypass` flag means no header is
// required.
//
// Dual base URL: when this module runs on the Next.js server (e.g. inside an
// async server component, or in a Docker container) the browser-facing
// `NEXT_PUBLIC_API_BASE_URL=http://localhost:8000` does NOT reach the backend
// container — `localhost` resolves to the Next.js container itself. Use the
// internal compose hostname (`http://backend:8000`) via `API_BASE_URL` instead.
// In the browser, `process.env.API_BASE_URL` is undefined (only `NEXT_PUBLIC_*`
// vars are inlined client-side) so we naturally fall back to the public URL.

const isServer = typeof window === "undefined";
const API_BASE_URL = isServer
  ? process.env.API_BASE_URL ??
    process.env.NEXT_PUBLIC_API_BASE_URL ??
    "http://localhost:8000"
  : process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

// Server-side Basic Auth pass-through. When the pilot-demo deploy gates the
// backend behind Basic Auth (BASIC_AUTH_USER/PASSWORD), Next.js server
// components must forward those credentials on every SSR fetch — the browser
// already solved its own prompt against the frontend edge middleware, but the
// frontend→backend hop is a separate origin and therefore a separate gate.
// In the browser bundle these env vars are not inlined (no NEXT_PUBLIC_*
// prefix), so `SSR_AUTH_HEADER` is naturally empty client-side.
const SSR_AUTH_HEADER: string | null = (() => {
  if (!isServer) return null;
  const u = process.env.BASIC_AUTH_USER;
  const p = process.env.BASIC_AUTH_PASSWORD;
  if (!u || !p) return null;
  const encoded = Buffer.from(`${u}:${p}`).toString("base64");
  return `Basic ${encoded}`;
})();

export class ApiError extends Error {
  constructor(public status: number, public body: unknown) {
    super(`API ${status}`);
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const baseHeaders: Record<string, string> = {
    "Content-Type": "application/json",
  };
  if (SSR_AUTH_HEADER) {
    baseHeaders["Authorization"] = SSR_AUTH_HEADER;
  }
  const res = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    headers: {
      ...baseHeaders,
      ...(init?.headers ?? {}),
    },
    cache: "no-store",
  });
  if (!res.ok) {
    let body: unknown = null;
    try {
      body = await res.json();
    } catch {
      // ignore
    }
    throw new ApiError(res.status, body);
  }
  if (res.status === 204) return undefined as T;
  return (await res.json()) as T;
}

export const api = {
  get: <T>(path: string) => request<T>(path),
  post: <T>(path: string, body: unknown) =>
    request<T>(path, { method: "POST", body: JSON.stringify(body) }),
  patch: <T>(path: string, body: unknown) =>
    request<T>(path, { method: "PATCH", body: JSON.stringify(body) }),
  delete: <T>(path: string) => request<T>(path, { method: "DELETE" }),
};
