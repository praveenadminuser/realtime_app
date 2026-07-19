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

## Not built yet

Deliberately out of scope for this server-side-only pass. Naming them so the gaps are
explicit, not accidental:

- **No refresh tokens.** When the 30-minute access token expires, the client must log in
  again. The standard fix is a long-lived refresh token (stored server-side, revocable)
  that mints new access tokens — that's the next iteration.
- **No logout / revocation.** A stateless JWT is valid until `exp` no matter what. Real
  logout needs a server-side denylist of token ids (`jti`) or the refresh-token model.
- **No roles / permissions.** Every authenticated user is equal. RBAC would add a `role`
  claim and a dependency like `require_role("admin")`.
- **No client-side integration.** The React UI does not log in or store a token yet — this
  pass is server-only. When it's added: send `Authorization: Bearer` from
  [`ui/src/api/client.ts`](ui/src/api/client.ts), and think hard about **where the token
  lives** (an in-memory variable is safest; `localStorage` is XSS-readable; an
  `HttpOnly` cookie needs CSRF protection).
- **No rate limiting on login.** A brute-force protection (lockout / backoff) belongs in
  front of `/auth/login` before this is public.

---

## What is verified

The modules **compile** and the routes register (`/auth/login`, `/users/me`). The flow has
**not been run end to end** — no login exercised against a live database in this pass.
Rebuild the backend image and run the migration first (the `users` table must exist), then
walk the curl sequence above. As always with this project: a green Compose build does not
mean the Kubernetes image is fresh — rebuild the `realtime-app` tag and
`kubectl rollout restart` before testing in the cluster.