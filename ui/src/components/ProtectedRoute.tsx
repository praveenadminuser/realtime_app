// Wraps any route that requires login. Waits out the initial token check, then either
// renders the page or bounces to /login.
import type { ReactNode } from "react";
import { Navigate } from "react-router-dom";

import { useAuth } from "../auth/useAuth";

export function ProtectedRoute({ children }: { children: ReactNode }) {
  const { status } = useAuth();

  // Don't decide until the stored token has been validated — otherwise a logged-in user
  // sees a flash of the login page on every refresh.
  if (status === "loading") {
    return <p className="page">Loading…</p>;
  }
  if (status === "anonymous") {
    return <Navigate to="/login" replace />;
  }
  return <>{children}</>;
}