// Frontend twin of app/routers/messages.py. A protected resource — the bearer token
// attached by client.ts is what gets these past the router's auth dependency.
import type { Message } from "../types/message";
import { apiFetch } from "./client";

export function listMessages(limit = 20): Promise<Message[]> {
  return apiFetch<Message[]>(`/messages?limit=${limit}`);
}