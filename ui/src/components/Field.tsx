// A labelled input. The reusable, presentational layer — knows nothing about the API
// or registration, so it's shared by every future form.
interface FieldProps {
  label: string;
  name: string;
  value: string;
  onChange: (value: string) => void;
  type?: string;
  required?: boolean;
  autoComplete?: string;
}

export function Field({
  label,
  name,
  value,
  onChange,
  type = "text",
  required = false,
  autoComplete,
}: FieldProps) {
  return (
    <label className="field">
      <span>
        {label}
        {required && <em aria-hidden> *</em>}
      </span>
      <input
        name={name}
        type={type}
        value={value}
        required={required}
        autoComplete={autoComplete}
        onChange={(e) => onChange(e.target.value)}
      />
    </label>
  );
}
