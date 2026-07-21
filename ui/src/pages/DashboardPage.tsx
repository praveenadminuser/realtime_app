import { useState } from "react";

import { ApiError } from "../api/client";
import { listMessages } from "../api/messages";
import { useAuth } from "../auth/useAuth";
import type { Message } from "../types/message";

export function DashboardPage() {
  const { user, logout } = useAuth();
  const [messages, setMessages] = useState<Message[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function loadMessages() {
    setBusy(true);
    setError(null);
    try {
      setMessages(await listMessages());
    } catch (err) {
      // If the token expired mid-session, the fetch 401s. Log out so ProtectedRoute
      // sends us back to /login, rather than showing a stuck error.
      if (err instanceof ApiError && err.status === 401) {
        await logout();
        return;
      }
      setError(err instanceof ApiError ? err.message : "Failed to load messages.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <main className="page">
      <div className="topbar">
        <span>
          Logged in as <strong>{user?.username}</strong>
        </span>
        <button className="secondary" onClick={() => logout()}>
          Log out
        </button>
      </div>

      <h1>Dashboard</h1>

      <button onClick={loadMessages} disabled={busy}>
        {busy ? "Loading…" : "Show messages"}
      </button>

      {error && <p className="error" role="alert">{error}</p>}

      {messages !== null &&
        (messages.length === 0 ? (
          <p className="muted">No messages yet.</p>
        ) : (
          <table className="table">
            <thead>
              <tr>
                <th>ID</th>
                <th>Message</th>
                <th>Created</th>
              </tr>
            </thead>
            <tbody>
              {messages.map((m) => (
                <tr key={m.id}>
                  <td>{m.id}</td>
                  <td>{m.body}</td>
                  <td>{new Date(m.created_at).toLocaleString()}</td>
                </tr>
              ))}
            </tbody>
          </table>
        ))}
    </main>
  );
}
