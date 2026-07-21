// The register feature's view. Holds form state, delegates the request to useRegister,
// and renders one of three states: the form, a submit-in-progress button, or success.
import { useState, type FormEvent } from "react";
import { Link } from "react-router-dom";

import { Field } from "../../components/Field";
import { useRegister } from "./useRegister";

const EMPTY = {
  username: "",
  email: "",
  password: "",
  first_name: "",
  last_name: "",
  date_of_birth: "",
};

export function RegisterForm() {
  const { status, error, user, submit } = useRegister();
  const [form, setForm] = useState(EMPTY);

  const set = (field: keyof typeof EMPTY) => (value: string) =>
    setForm((f) => ({ ...f, [field]: value }));

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    await submit({
      username: form.username,
      email: form.email,
      password: form.password,
      // Empty optional fields go as null, not "" — matches the nullable columns.
      first_name: form.first_name || null,
      last_name: form.last_name || null,
      date_of_birth: form.date_of_birth || null,
    });
  }

  if (status === "success" && user) {
    return (
      <div className="card success">
        <h2>Welcome, {user.username} 🎉</h2>
        <p>
          Account created with id <strong>{user.id}</strong>. You can now{" "}
          <Link to="/login">sign in</Link>.
        </p>
      </div>
    );
  }

  return (
    <form className="card" onSubmit={onSubmit} noValidate>
      <Field label="Username" name="username" value={form.username}
        onChange={set("username")} required autoComplete="username" />
      <Field label="Email" name="email" type="email" value={form.email}
        onChange={set("email")} required autoComplete="email" />
      <Field label="Password" name="password" type="password" value={form.password}
        onChange={set("password")} required autoComplete="new-password" />
      <div className="row">
        <Field label="First name" name="first_name" value={form.first_name}
          onChange={set("first_name")} autoComplete="given-name" />
        <Field label="Last name" name="last_name" value={form.last_name}
          onChange={set("last_name")} autoComplete="family-name" />
      </div>
      <Field label="Date of birth" name="date_of_birth" type="date"
        value={form.date_of_birth} onChange={set("date_of_birth")} />

      {error && <p className="error" role="alert">{error}</p>}

      <button type="submit" disabled={status === "submitting"}>
        {status === "submitting" ? "Creating account…" : "Create account"}
      </button>
    </form>
  );
}
