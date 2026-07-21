import { Link } from "react-router-dom";

import { RegisterForm } from "../features/register/RegisterForm";

export function RegisterPage() {
  return (
    <main className="page">
      <h1>Create your account</h1>
      <p className="subtitle">Register for the Realtime App.</p>
      <RegisterForm />
      <p className="muted">
        Already have an account? <Link to="/login">Sign in</Link>
      </p>
    </main>
  );
}
