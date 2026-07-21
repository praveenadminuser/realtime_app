# Authentication — OAuth2 password flow + JWT

Server-side auth: users log in with username + password and receive a signed JWT, which
they send on every subsequent request. This covers how it works, how to use it, the
security decisions, and — importantly — what is deliberately **not** built yet.

---

## The flow in one picture

```
1. POST /auth/login            2. server verifies password,        3. client sends the token
   username + password  ─────►    signs a JWT with a secret  ─────►   Authorization: Bearer <jwt>
   (form-encoded)                 { sub: <user id>, exp }             on every protected request
                                        │                                     │
                                        ▼                                     ▼
                                 returns { access_token }            server verifies the SIGNATURE
                                                                     (no DB lookup for the token itself)
```

The defining property: **the token is stateless.** The server stores nothing when it
issues one. On the next request it doesn't look the token up in a database — it
recomputes the signature with its secret and trusts the token if they match. That's what
makes JWT scale across many pods (any pod can validate any token) and it's also the source
of its main limitation (you can't un-issue one — see [Not built yet](#not-built-yet)).

---

## The pieces

| File | Role |
|------|------|
| [`app/core/security.py`](app/core/security.py) | `create_access_token` / `decode_access_token` (+ password hashing). The only file that touches PyJWT. |
| [`app/config.py`](app/config.py) | `jwt_secret`, `jwt_algorithm`, `access_token_expire_minutes`. |
| [`app/schemas/auth.py`](app/schemas/auth.py) | `Token` — the `{access_token, token_type}` response. |
| [`app/services/user_service.py`](app/services/user_service.py) | `authenticate_user` — username + password → User or None. |
| [`app/routers/auth.py`](app/routers/auth.py) | `POST /auth/login`. |
| [`app/dependencies.py`](app/dependencies.py) | `get_current_user` / `get_current_active_user` — the gate protected routes sit behind. |
| [`app/routers/users.py`](app/routers/users.py) | `GET /users/me` — an example protected endpoint. |

The layering is the same as everywhere else: the **router** does HTTP, the **service**
does logic, **core/security** does crypto. No endpoint touches PyJWT; no crypto code
touches a request object.

---

## Endpoints

### `POST /auth/login` — get a token

**Form-encoded, not JSON.** The OAuth2 password spec mandates form fields, and FastAPI's
`OAuth2PasswordRequestForm` parses exactly `username` and `password`. (This is why
`python-multipart` is a dependency.)

```bash
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=alice&password=secret123"
# { "access_token": "eyJhbGci...", "token_type": "bearer" }
```

Wrong username or wrong password both return the same `401 Incorrect username or
password` — see [Security notes](#security-notes) for why.

### `GET /users/me` — a protected endpoint

```bash
TOKEN="eyJhbGci..."
curl http://localhost:8000/users/me -H "Authorization: Bearer $TOKEN"
# { "id": 1, "username": "alice", ... }

curl -i http://localhost:8000/users/me            # no token
# HTTP/1.1 401 Unauthorized
```

Any route that adds `Depends(get_current_active_user)` becomes protected the same way.

---

## Trying it in Swagger UI

`http://localhost:8000/docs` understands this flow natively:

1. Click **Authorize** (top right).
2. Enter a registered user's username + password. Swagger POSTs to `/auth/login` — it
   knows the URL from `OAuth2PasswordBearer(tokenUrl="auth/login")` in
   [`dependencies.py`](app/dependencies.py).
3. Now every "Try it out" on a protected route sends the `Authorization: Bearer` header
   automatically. `GET /users/me` returns your user; the lock icon marks protected routes.

End-to-end from scratch:

```bash
# register (from the UI or curl)
curl -X POST http://localhost:8000/users -H "Content-Type: application/json" \
  -d '{"username":"alice","email":"alice@example.com","password":"secret123"}'

# log in -> capture the token
TOKEN=$(curl -s -X POST http://localhost:8000/auth/login \
  -d "username=alice&password=secret123" | python -c "import sys,json;print(json.load(sys.stdin)['access_token'])")

# use it
curl http://localhost:8000/users/me -H "Authorization: Bearer $TOKEN"
```

---

## Two ways to extract the token: `OAuth2PasswordBearer` vs `HTTPBearer`

Protected routes recognise the caller from the header `Authorization: Bearer <jwt>`. The
dependency that pulls that token out of the request is a **security scheme**, and FastAPI
offers two. **Both read the exact same header** — the difference is what they return, how
they appear in Swagger, and what status they raise when the token is missing.

This project uses `OAuth2PasswordBearer`. `HTTPBearer` is documented here as the
alternative.

| | `OAuth2PasswordBearer` (in use) | `HTTPBearer` |
|---|---|---|
| Reads | `Authorization: Bearer <jwt>` | `Authorization: Bearer <jwt>` (identical) |
| Swagger **Authorize** dialog | **username + password** fields; Swagger calls `/auth/login` for you and stores the token | a single box where you **paste a token** you already obtained |
| Needs `tokenUrl`? | yes — it's how Swagger knows where to log in | no |
| Dependency gives you | the raw token **string** | an `HTTPAuthorizationCredentials` object (`.scheme`, `.credentials`) |
| Missing token → | **401** Unauthorized + `WWW-Authenticate: Bearer` | **403** Forbidden, no header (unless `auto_error=False`) |
| Best when | **your app issues the tokens** (our case) | tokens come from an **external** identity provider, or you prefer pasting |

**Why we use `OAuth2PasswordBearer`.** Because this app owns `/auth/login`, the OAuth2
scheme lets Swagger *perform the login itself* — you type username/password once in the
Authorize dialog and every protected "Try it out" just works. That mirrors the real UI
flow (enter credentials → get token → send bearer) with no copy-paste.

### What changes to switch to `HTTPBearer`

Only [`app/dependencies.py`](app/dependencies.py) changes. `/auth/login` and everything
else stay exactly the same — how you *extract* the token is independent of how login
*accepts* credentials.

```python
# before — OAuth2PasswordBearer
from fastapi.security import OAuth2PasswordBearer
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

async def get_current_user(
    token: str = Depends(oauth2_scheme),               # raw string
    session: AsyncSession = Depends(get_session),
) -> User:
    claims = decode_access_token(token)
    ...
```

```python
# after — HTTPBearer (auto_error=False keeps our 401 instead of a silent 403)
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
bearer_scheme = HTTPBearer(auto_error=False)

async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    session: AsyncSession = Depends(get_session),
) -> User:
    if credentials is None:                            # header absent
        raise credentials_error                        # your existing 401
    token = credentials.credentials                    # <-- unwrap the string
    claims = decode_access_token(token)
    ...
```

Three consequences worth knowing:

1. **Swagger becomes a paste-token box.** With no `tokenUrl`, Swagger can't log you in.
   You call `POST /auth/login` yourself (curl or its own "Try it out"), copy the
   `access_token`, and paste it into Authorize. Swagger stops doing the login step.
2. **Missing-token status flips 401 → 403.** A FastAPI quirk: bare `HTTPBearer` returns
   403 (no `WWW-Authenticate`) when the header is absent, where `OAuth2PasswordBearer`
   returns 401. `HTTPBearer(auto_error=False)` + the explicit `None` check above restores
   the 401 — otherwise the downgrade surprises clients that key off 401.
3. **`/auth/login` is untouched.** It still parses form-encoded username/password via
   `OAuth2PasswordRequestForm`. Switching login to a JSON body is a *separate*, optional
   decision, unrelated to the bearer scheme.

**Rule of thumb:** if the API issues its own tokens, prefer `OAuth2PasswordBearer` for the
better Swagger experience. Reach for `HTTPBearer` when your API only *verifies* tokens
minted by someone else (an external IdP, Cognito, Auth0), where there's no local
`/auth/login` for Swagger to call anyway.

---

## What's inside the token

A JWT is three base64url parts, `header.payload.signature`. Ours carries:

```json
{ "sub": "1", "iat": 1721400000, "exp": 1721401800 }
```

- **`sub`** (subject) — the user id, as a string. The auth dependency casts it back to
  int and loads the user.
- **`iat`** — issued-at.
- **`exp`** — expiry. PyJWT rejects the token automatically once this passes.

**The payload is signed, not encrypted.** Anyone can base64-decode it and read the
claims — paste one into <https://jwt.io> to see. So never put a secret (password, card
number) in a JWT. The signature guarantees *integrity* (nobody tampered with it), not
*confidentiality*.

---

## Security notes

**The signing key is everything.** Whoever holds `jwt_secret` can forge a valid token for
any user. It is a top-tier secret — on AWS it belongs in the same Secrets Manager entry as
the DB credentials, delivered by the same External Secrets flow (see [EKS.md](EKS.md)).
The code ships an insecure default (`dev-only-insecure-change-me`) so local dev works, and
[`main.py`](app/main.py) logs a **loud warning** at startup if it's still in use, so it
can't quietly reach a real environment.

**The algorithm is pinned on verify.** `decode_access_token` passes
`algorithms=[jwt_algorithm]` explicitly. If you instead trusted the algorithm named in the
token's own header, an attacker could send `alg: "none"` (unsigned) or downgrade
`RS256`→`HS256` and forge tokens. Always dictate the algorithm on the verifying side.

**Login doesn't leak which half was wrong.** "No such user" and "wrong password" return
the identical 401, and [`authenticate_user`](app/services/user_service.py) verifies against
a dummy hash when the user is missing so both paths take the **same time**. Otherwise the
response time is an oracle for enumerating valid usernames.

**Passwords are bcrypt hashes, never stored plaintext.** Covered in the register flow; the
`password_hash` column holds a one-way digest and login compares hashes.

**HS256 vs RS256.** HS256 (current) uses one shared secret to both sign and verify — fine
when a single service does both, which is our case. Move to RS256 (sign with a private
key, verify with a public one) when *other* services need to validate tokens without being
able to mint them.

**Tokens are short-lived (30 min).** Because a stateless token can't be revoked before it
expires, a short lifetime is what caps the damage of a leaked one.

---

## Configuration

| Env var | Default | Notes |
|---------|---------|-------|
| `JWT_SECRET` | `dev-only-insecure-change-me` | **Must be overridden** everywhere but local. Generate: `openssl rand -hex 32`. |
| `JWT_ALGORITHM` | `HS256` | |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `30` | |

Locally, add to `.env.dev`. In Kubernetes, `JWT_SECRET` should ride in the
`postgres-credentials` Secret (or a dedicated auth Secret) so it arrives via `envFrom`
exactly like the DB values — never in the committed `app-config` ConfigMap, which is for
non-secret config only.

```bash
# generate a real secret
openssl rand -hex 32
```

---

## Client integration (the UI)

The React UI now does the full flow. Files mirror the backend:

- **Login** — [`pages/LoginPage.tsx`](ui/src/pages/LoginPage.tsx) → [`api/auth.ts`](ui/src/api/auth.ts)
  `login()` POSTs form-encoded credentials to `/auth/login` and stores the token.
- **Token attach** — [`api/client.ts`](ui/src/api/client.ts) adds `Authorization: Bearer`
  to every request from one place. A `401` clears the stored token.
- **Session state** — [`auth/AuthContext.tsx`](ui/src/auth/AuthContext.tsx) holds the
  current user; on load it validates a stored token by calling `/users/me`.
- **Route gating** — [`components/ProtectedRoute.tsx`](ui/src/components/ProtectedRoute.tsx)
  bounces anonymous users to `/login`.
- **Logout** — [`DashboardPage`](ui/src/pages/DashboardPage.tsx) calls
  `POST /auth/logout` then drops the local token.

**Logout is mostly client-side, by necessity.** `POST /auth/logout`
([`routers/auth.py`](app/routers/auth.py)) requires a valid token and logs the event, but
a stateless JWT stays cryptographically valid until `exp` — the server has nothing to
delete. The *real* logout is the client discarding the token so it stops sending it. True
server revocation needs a shared denylist of token ids (`jti`); an in-memory one breaks
across replicas (each pod has its own memory), so short token lifetimes are the pragmatic
substitute.

**Where the token lives:** `localStorage` (see [`auth/storage.ts`](ui/src/auth/storage.ts)),
chosen for surviving refresh. It is readable by any JS on the page, so an XSS bug leaks it
— the documented trade-off vs. in-memory (safest, lost on reload) or an `HttpOnly` cookie
(needs CSRF handling + a backend change). `storage.ts` is the single seam to swap it.

## Not built yet

Naming the remaining gaps so they're explicit, not accidental:

- **No refresh tokens.** When the 30-minute access token expires, the user must log in
  again. The standard fix is a long-lived refresh token (stored server-side, revocable)
  that mints new access tokens — the next iteration, and also what makes real logout work.
- **No server-side revocation.** As above: logout drops the client token but can't
  invalidate an already-issued JWT before `exp`.
- **No roles / permissions.** Every authenticated user is equal. RBAC would add a `role`
  claim and a dependency like `require_role("admin")`.
- **No rate limiting on login.** Brute-force protection (lockout / backoff) belongs in
  front of `/auth/login` before this is public.

---

## What is verified

The backend modules **compile** and the routes register (`/auth/login`, `/auth/logout`,
`/users/me`, protected `/messages`). The UI **has not been built or run** — `react-router-dom`
was added to `package.json` but not `npm install`ed, and no browser flow was exercised.

To verify end to end:
1. `cd ui && npm install` (pulls react-router-dom), then `npm run build` to shake out types.
2. Rebuild the backend image and run migration `0002` (the `users` table must exist).
3. Register → sign in → **Show messages** → log out, in the browser.

As always: a green Compose build does not mean the Kubernetes images are fresh — rebuild
**both** the `realtime-app` and `realtime-ui` tags and `kubectl rollout restart` before
testing in the cluster.