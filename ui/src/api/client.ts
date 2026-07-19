// The one module that talks HTTP. Every api/*.ts file goes through here, so retries,
// auth headers, or a base-URL change happen in exactly one place.

// Relative, deliberately. The browser resolves /api against whatever origin served
// the page, so the SAME build works in dev (Vite proxies /api -> :8000) and in the
// cluster (nginx proxies /api -> the backend Service). There is no API URL to
// configure per environment — the mirror of how the backend reads DB_HOST at runtime.
const BASE = "/api";

// A typed error so callers can branch on status (e.g. 409 = already registered)
// instead of parsing strings.
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
  const res = await fetch(`${BASE}${path}`, {
    headers: { "Content-Type": "application/json", ...(options.headers ?? {}) },
    ...options,
  });

  if (!res.ok) {
    throw new ApiError(res.status, await extractError(res));
  }
  if (res.status === 204) {
    return undefined as T; // No Content
  }
  return (await res.json()) as T;
}

// FastAPI errors come in two shapes: a plain {"detail": "..."} (our HTTPExceptions)
// and validation errors {"detail": [{msg, loc}, ...]} (422 from Pydantic). Flatten
// both into one readable string.
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
    // non-JSON body (e.g. an nginx 502) — fall through
  }
  return res.statusText || `Request failed (${res.status})`;
}
