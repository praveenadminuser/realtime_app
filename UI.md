# Frontend — React UI

The `ui/` app: a React single-page app that talks to the FastAPI backend. This covers
how it's structured, the one design decision everything rests on, and how to run it in
each environment.

---

## The one idea

> **A React app is not a service that "connects to the API." It is static files
> (HTML/JS/CSS) that run in the user's browser, and the _browser_ makes the API calls.**

The pod serving the UI never talks to the API pod. The user's browser does — from
outside the cluster. That single fact drives everything below: the proxy, the Dockerfile,
and why the UI Service is the public front door.

The corollary that removes a whole class of bugs: **the browser calls the _relative_ path
`/api/...`, never an absolute URL.** So the frontend never needs to know the backend's
address. Something on the same origin proxies `/api` onward — Vite in dev, nginx in the
cluster. One build runs everywhere, with no per-environment configuration.

This is the deliberate _inverse_ of the backend. FastAPI reads `DB_HOST` from the
environment at **runtime**, so one image points anywhere. A React build bakes
`import.meta.env.VITE_*` into the JS bundle at **build** time — frozen, unswappable at
container start. Relative paths sidestep that entirely: there is nothing to configure, so
there is nothing to bake. See [`ui/.env.example`](ui/.env.example).

---

## Directory structure

```
ui/
  src/
    api/                the ONLY layer that knows HTTP exists
      client.ts         fetch wrapper: base path /api, error flattening
      users.ts          registerUser() — twin of app/routers/users.py
    types/
      user.ts           TS interfaces — twin of app/schemas/user.py
    features/           one folder per feature, colocated
      register/
        RegisterForm.tsx  the view: form state + rendering
        useRegister.ts    the hook: request state (idle/submitting/success/error)
    components/         reusable, presentational (Field.tsx) — no API knowledge
    pages/              route-level screens (RegisterPage.tsx)
    App.tsx  main.tsx  index.css
  Dockerfile           multi-stage: node build -> nginx serves static
  nginx.conf           serves the SPA + proxies /api to the backend
  vite.config.ts       dev-only proxy: /api -> localhost:8000
  package.json  tsconfig*.json
```

### It mirrors the backend on purpose

| Backend (`app/`)     | Frontend (`ui/src/`)     | Role                         |
| -------------------- | ------------------------ | ---------------------------- |
| `routers/`           | `pages/` + `features/`   | the HTTP / UI surface        |
| `services/`          | `api/`                   | the one layer that does I/O  |
| `schemas/`           | `types/`                 | the data contract            |

`api/users.ts` is the twin of `routers/users.py`; `types/user.ts` the twin of
`schemas/user.py`. Add a login endpoint and you touch the same three layers on each side.
Everything else — components, pages — stays ignorant of HTTP.

### The layers, top to bottom

- **`pages/`** compose features and layout. No logic.
- **`features/`** own a slice of behaviour. The **component** holds form state and
  rendering; the **hook** (`useRegister`) owns the request lifecycle. Splitting them means
  the form doesn't change when you later swap in TanStack Query — only the hook does.
- **`api/`** is the single place that speaks HTTP. `client.ts` sets the `/api` base and
  flattens FastAPI's two error shapes (`{detail: "..."}` and the `422` validation array)
  into one string. `users.ts` has one function per backend endpoint.
- **`types/`** is the contract, kept beside the API layer so drift is obvious.

---

## How the browser reaches the API

Same-origin. The browser only ever calls the origin that served the page, so there is **no
CORS** and **no API URL in the bundle**.

```
DEV                                    CLUSTER
browser :5173                          browser --> UI LoadBalancer :80
  |  fetch("/api/users")                 |  fetch("/api/users")
  v                                      v
Vite dev server                        nginx (in the UI pod)
  proxy /api -> localhost:8000           proxy /api/ -> http://realtime-app:8080/
  (strips /api)                          (strips /api via trailing-slash proxy_pass)
  v                                      v
FastAPI :8000                          realtime-app Service :8080 -> pod :8000
```

Both sides **strip the `/api` prefix**, because the backend mounts its routes at the root
(`/users`, `/health`), not under `/api`. Dev does it with a `rewrite` in
[`vite.config.ts`](ui/vite.config.ts); the cluster does it with the trailing slash on
`proxy_pass` in [`ui/nginx.conf`](ui/nginx.conf). Same behaviour, two mechanisms.

**Consequence for Kubernetes:** the UI Service is now the public `LoadBalancer`, and its
nginx reaches the backend over the internal `realtime-app` Service. The backend therefore
no longer needs to be internet-facing — on EKS you could downgrade `realtime-app` to
`ClusterIP` and expose only the UI. (Left as `LoadBalancer` for now.)

---

## Running it

### Dev — the fast loop

```bash
# terminal 1: backend (see DATABASE.md)
docker compose up -d
docker compose run --rm api alembic upgrade head

# terminal 2: frontend
cd ui
npm install        # first time only
npm run dev        # http://localhost:5173, hot reload
```

Open http://localhost:5173, fill the form, submit. The request goes
`/api/users` → Vite → `localhost:8000/users` → Postgres. No Docker needed for the UI in
dev, and edits reload instantly.

### Docker — the production image

```bash
cd ui
docker build -t realtime-ui:0.1.0 .
docker run --rm -p 8080:80 realtime-ui:0.1.0
```

The build is **multi-stage**: `node:20-alpine` compiles the bundle, then only the static
files are copied into `nginx:1.27-alpine`. The final image (~50 MB) contains no Node, no
source, no `node_modules` — just a static file server.

> Standalone, the container serves the UI but `/api` calls 502, because `realtime-app`
> only resolves inside Kubernetes. To exercise the whole stack locally, use the dev loop
> above or the k8s local overlay below.

### Kubernetes — local

```bash
docker build -t realtime-ui:0.1.0 ./ui
docker build -t realtime-app:0.2.0 .        # backend, if not already built
kubectl apply -k k8s/overlays/local
kubectl get pods
```

The UI is part of `k8s/base/`, so every overlay includes it. Reach it at the UI Service's
`localhost` (Docker Desktop maps the LoadBalancer there).

### Kubernetes — EKS

The AWS overlays rewrite `realtime-ui` to its ECR URI and set `imagePullPolicy: Always`,
exactly like the backend. Push the image alongside the API:

```bash
docker build -t $ECR_REPO/realtime-ui:0.1.0 ./ui
docker push $ECR_REPO/realtime-ui:0.1.0
kubectl apply -k k8s/overlays/dev
```

See [EKS.md](EKS.md) for the ECR/cluster setup. On EKS, prefer a single **Ingress** (ALB)
routing `/` to the UI Service and `/api` to the backend, rather than two LoadBalancers.

---

## The stack, and why

| Choice           | Why                                                                  |
| ---------------- | -------------------------------------------------------------------- |
| **Vite**         | The current default. Create React App is deprecated. Instant HMR.    |
| **React + TS**   | The API contract is typed; the frontend should match it (`types/`).  |
| **nginx**        | Tiny, battle-tested static server; does the `/api` proxy in one file. |
| no data lib yet  | One form doesn't need TanStack Query. Add it in `useRegister` when it does. |

---

## Health probes

nginx serves its own `/healthz` (see [`ui/nginx.conf`](ui/nginx.conf)), and both k8s
probes hit **that**, not the backend. The UI serves static files independently of the API —
if the database is down, the page still loads and the browser shows the API error.
Coupling the UI's readiness to the backend would take the UI offline for no reason.

---

## Adding the next feature (the pattern)

Say `GET /users/{id}`:

1. **`types/user.ts`** — already has `UserRead`; reuse it.
2. **`api/users.ts`** — add `getUser(id) => apiFetch<UserRead>(\`/users/${id}\`)`.
3. **`features/profile/`** — a component + a `useUser` hook.
4. **`pages/ProfilePage.tsx`** — render it.

No other file changes. That containment is the whole reason for the layering — the same
property the backend's routers/services/schemas split gives you.

---

## What is verified

Honest disclosure, consistent with the other docs: the **manifests build**
(`kubectl kustomize` passes for every overlay). The **UI itself has not been run** — no
`npm install`, no `npm run build`, no browser. The code compiles in principle and the
types line up with the backend schemas, but expect to shake out a nit on the first real
build.
