// The one module that talks HTTP. Every api/*.ts file goes through here, so the bearer
// token, error handling, and base URL live in exactly one place.
import { clearToken, getToken } from "../auth/storage";

// Relative, deliberately. The browser resolves /api against whatever origin served the
// page, so the SAME build works in dev (Vite proxies /api) and in the cluster (nginx
// proxies /api). Nothing to configure per environment.
const BASE = "/api";

export class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
    this.name = "ApiError";
  }
}

export async function apiFetch<T>(
  path: string,
  options: RequestInit = {},
): Promise<T> {
  // The login endpoint sends form-encoded data (URLSearchParams). For that, let the
  // browser set Content-Type (application/x-www-form-urlencoded) itself; everything else
  // is JSON. Setting JSON on a URLSearchParams body would make FastAPI reject the form.
  const isForm = options.body instanceof URLSearchParams;
  const headers: Record<string, string> = { ...(options.headers as Record<string, string>) };
  if (!isForm) {
    headers["Content-Type"] = "application/json";
  }

  // Attach the bearer token if we have one. THIS is how every protected call
  // authenticates — the server reads this header (see dependencies.py).
  const token = getToken();
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  const res = await fetch(`${BASE}${path}`, { ...options, headers });

  // A 401 means the token is missing/expired/invalid. Drop it so the app falls back to
  // the anonymous state; the caller decides whether to redirect to /login.
  if (res.status === 401) {
    clearToken();
  }

  if (!res.ok) {
    throw new ApiError(res.status, await extractError(res));
  }
  if (res.status === 204) {
    return undefined as T;
  }
  return (await res.json()) as T;
}

// FastAPI errors come in two shapes: {"detail": "..."} (our HTTPExceptions) and the 422
// validation array {"detail": [{msg, loc}, ...]}. Flatten both to one readable string.
async function extractError(res: Response): Promise<string> {
  try {
    const body = await res.json();
    if (typeof body.detail === "string") {
      return body.detail;
    }
    if (Array.isArray(body.detail)) {
      return body.detail
        .map((d: { loc?: (string | number)[]; msg: string }) => {
          const field = d.loc?.[d.loc.length - 1];
          return field ? `${field}: ${d.msg}` : d.msg;
        })
        .join(", ");
    }
  } catch {
    // non-JSON body (e.g. an nginx 502)
  }
  return res.statusText || `Request failed (${res.status})`;
}