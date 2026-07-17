// The frontend twin of app/routers/users.py. One function per backend endpoint.
// Add login() here when the backend grows POST /auth/login — nothing else changes shape.
import type { UserCreate, UserRead } from "../types/user";
import { apiFetch } from "./client";

export function registerUser(payload: UserCreate): Promise<UserRead> {
  return apiFetch<UserRead>("/users", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}
