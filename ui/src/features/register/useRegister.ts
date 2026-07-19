// The bridge between the form and the API. Owns request state (idle/submitting/
// success/error) so the component stays presentational. When you add TanStack Query
// later, this hook is the one file that changes — the form doesn't.
import { useState } from "react";

import { ApiError } from "../../api/client";
import { registerUser } from "../../api/users";
import type { UserCreate, UserRead } from "../../types/user";

type Status = "idle" | "submitting" | "success" | "error";

export function useRegister() {
  const [status, setStatus] = useState<Status>("idle");
  const [error, setError] = useState<string | null>(null);
  const [user, setUser] = useState<UserRead | null>(null);

  async function submit(payload: UserCreate): Promise<UserRead | null> {
    setStatus("submitting");
    setError(null);
    try {
      const created = await registerUser(payload);
      setUser(created);
      setStatus("success");
      return created;
    } catch (e) {
      // 409 carries the backend's "username already registered" message; anything
      // else falls back to a generic line so a stack trace never reaches the user.
      setError(e instanceof ApiError ? e.message : "Something went wrong. Try again.");
      setStatus("error");
      return null;
    }
  }

  return { status, error, user, submit };
}
