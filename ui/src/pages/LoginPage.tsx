import { useState, type FormEvent } from "react";
import { Link, useNavigate } from "react-router-dom";

import { ApiError } from "../api/client";
import { useAuth } from "../auth/useAuth";
import { Field } from "../components/Field";

export function LoginPage() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      await login(username, password);
      navigate("/"); // to the protected dashboard
    } catch (err) {
      // The backend returns one message for bad-user AND bad-password on purpose.
      setError(err instanceof ApiError ? err.message : "Login failed. Try again.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <main className="page">
      <h1>Sign in</h1>
      <form className="card" onSubmit={onSubmit}>
        <Field label="Username" name="username" value={username}
          onChange={setUsername} required autoComplete="username" />
        <Field label="Password" name="password" type="password" value={password}
          onChange={setPassword} required autoComplete="current-password" />
        {error && <p className="error" role="alert">{error}</p>}
        <button type="submit" disabled={busy}>
          {busy ? "Signing in…" : "Sign in"}
        </button>
      </form>
      <p className="muted">
        No account? <Link to="/register">Register</Link>
      </p>
    </main>
  );
}