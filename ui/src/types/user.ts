// The TypeScript twin of app/schemas/user.py. When the backend contract changes,
// these change with it — keeping them side by side is the whole point of a types/ layer.

// Matches UserCreate — what POST /users accepts.
export interface UserCreate {
  username: string;
  email: string;
  password: string;
  first_name?: string | null;
  last_name?: string | null;
  date_of_birth?: string | null; // ISO date, "YYYY-MM-DD"
}

// Matches UserRead — what the API returns. Note: no password/hash field exists here,
// mirroring the backend, which never sends it.
export interface UserRead {
  id: number;
  username: string;
  email: string;
  first_name: string | null;
  last_name: string | null;
  date_of_birth: string | null;
  is_active: boolean;
  created_at: string;
}
