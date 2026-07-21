// The ONE place the token is read from / written to. Everything else (the API client,
// the auth context) goes through here, so changing WHERE the token lives is a one-file
// edit.
//
// ⚠️ Storage choice, and it's a real security trade-off:
//   localStorage  — survives refresh (good UX), but readable by ANY JavaScript on the
//                   page, so an XSS bug leaks the token. This is what we use.
//   in-memory     — safest (an XSS can't read a closure variable as easily, and it's
//                   gone on refresh), but the user is logged out every reload.
//   HttpOnly cookie — JS can't read it at all (best against XSS), but needs CSRF
//                   protection and a backend change to set/clear the cookie.
// localStorage is the pragmatic default for a bearer-token SPA; revisit if this app
// ever handles sensitive data. See AUTH.md.
const KEY = "realtime.token";

export const getToken = (): string | null => localStorage.getItem(KEY);
export const setToken = (token: string): void => localStorage.setItem(KEY, token);
export const clearToken = (): void => localStorage.removeItem(KEY);