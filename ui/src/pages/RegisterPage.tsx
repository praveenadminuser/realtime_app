// A route-level screen. Pages compose features and layout; they hold no logic
// themselves. When you add routing (react-router), each route renders a page like this.
import { RegisterForm } from "../features/register/RegisterForm";

export function RegisterPage() {
  return (
    <main className="page">
      <h1>Create your account</h1>
      <p className="subtitle">Register for the Realtime App.</p>
      <RegisterForm />
    </main>
  );
}
