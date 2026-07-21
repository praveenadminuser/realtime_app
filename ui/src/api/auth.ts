// Frontend twin of app/routers/auth.py.
import type { Token } from "../types/auth";
import type { UserRead } from "../types/user";
import { apiFetch } from "./client";

export function login(username: string, password: string): Promise<Token> {
  // OAuth2 password flow: the backend expects FORM fields, not JSON. URLSearchParams
  // makes the browser send application/x-www-form-urlencoded (see client.ts).
  const body = new URLSearchParams({ username, password });
  return apiFetch<Token>("/auth/login", { method: "POST", body });
}

export function logout(): Promise<{ detail: string }> {
  // Server-side this is mostly a formality (stateless JWT) — the real logout is the
  // client dropping the token. See the note in app/routers/auth.py.
  return apiFetch<{ detail: string }>("/auth/logout", { method: "POST" });
}

export function getMe(): Promise<UserRead> {
  // Also doubles as "is my stored token still valid?" — a 401 here means log out.
  return apiFetch<UserRead>("/users/me");
}