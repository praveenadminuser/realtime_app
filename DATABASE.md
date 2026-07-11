# Postgres — Local, Kubernetes, and RDS

How the app talks to a database, and how the same code reaches a container on your
laptop and an RDS instance in AWS without a single `if environment == "prod"`.

---

## The one idea

Everything below rests on one design decision:

> **The app knows nothing about where its database is. It reads `DATABASE_URL` and connects.**

```
docker compose      DATABASE_URL=postgresql+asyncpg://realtime:realtime@db:5432/realtime
local Kubernetes    DATABASE_URL=postgresql+asyncpg://realtime:realtime@postgres:5432/realtime
AWS EKS             DATABASE_URL=postgresql+asyncpg://appuser:••••@mydb.abc.eu-west-1.rds.amazonaws.com:5432/realtime
```

Three environments, three values, **zero code changes**. Only the *host* differs, and
in every case it's a name resolved by DNS — a Compose service name, a Kubernetes
Service name, an AWS endpoint. Never an IP, never `localhost`.

If you find yourself adding an environment check to the app, something has gone wrong.
The environment belongs in the Secret, not in the code.

---

## The pieces

| File | Job |
|------|-----|
| [`app/config.py`](app/config.py) | Reads `DATABASE_URL` (+ `DB_SSL`, pool sizes) from the environment. The only place env vars are touched. |
| [`app/db.py`](app/db.py) | Async engine, connection pool, `get_session()` dependency. Knows about connections, not tables. |
| [`app/models.py`](app/models.py) | The `Message` ORM model. **Describes** the table in Python. Emits no DDL, ever. |
| [`alembic/versions/`](alembic/versions/) | The actual `CREATE TABLE`. The only thing that changes the schema. |
| [`docker-compose.yml`](docker-compose.yml) | Local dev: app + Postgres in one command. |
| [`k8s/postgres.yaml`](k8s/postgres.yaml) | Postgres in local Kubernetes. **Deleted on EKS** — replaced by RDS. |
| [`k8s/migration-job.yaml`](k8s/migration-job.yaml) | Runs `alembic upgrade head` as a one-shot Job. Same file works against RDS. |

### Where does the table actually get created?

The single most common confusion. **`models.py` does not create the table.** It only
describes it. The `CREATE TABLE` lives in the Alembic migration and runs only when you
say so:

```bash
alembic upgrade head
```

Skip that and the app starts perfectly, `/health` returns 200, and your first
`POST /messages` dies with `relation "messages" does not exist`.

Why not SQLAlchemy's `Base.metadata.create_all()`, which so many tutorials call on
startup? Because it only ever does `CREATE TABLE IF NOT EXISTS`. It cannot **alter** an
existing table. The day you add a column, `create_all()` sees the table already exists,
does nothing, and the app crashes on a column Postgres has never heard of. Against RDS
you cannot drop the table and start over. Schema *change*, not schema *creation*, is the
real problem — which is what Alembic solves.

Alembic keeps a one-row `alembic_version` table recording which revision the database is
at. That's how `upgrade head` knows what's left to apply, and why running it twice is a
safe no-op.

---

## 1. Local — Docker Compose

The fast loop. Use this for day-to-day development.

```bash
docker compose up --build -d
docker compose run --rm api alembic upgrade head    # create the schema — required once
```

Verify:

```bash
curl http://localhost:8000/health/ready
# {"status":"ready","database":"ok"}

curl -X POST http://localhost:8000/messages \
  -H "Content-Type: application/json" -d '{"body":"hello"}'
# {"id":1,"body":"hello","created_at":"..."}

curl http://localhost:8000/messages
```

Look inside the database:

```bash
docker compose exec db psql -U realtime -d realtime -c "\d messages"
docker compose exec db psql -U realtime -d realtime -c "select * from alembic_version;"
```

Tear down:

```bash
docker compose down        # stop, keep the data (named volume survives)
docker compose down -v     # stop and WIPE the data
```

### Why the compose file looks like it does

**`DATABASE_URL` host is `db`, not `localhost`.** `db` is the Compose service name,
resolved by Compose's internal DNS. Inside the `api` container, `localhost` *is* the api
container — there's no Postgres there. This is the same idea as a Kubernetes Service
name, which is why it transfers unchanged.

**`depends_on: condition: service_healthy`**, not a bare `depends_on`. Plain `depends_on`
only waits for the container to *exist*, not to be *usable* — and Postgres accepts
connections for a moment while still initialising, then drops them. The `pg_isready`
healthcheck is the honest signal.

**A named volume (`pgdata`).** Without it, the database dies with the container. A
container's filesystem is not storage.

---

## 2. Local Kubernetes (Docker Desktop)

Slower loop, but it exercises the real wiring — Secret → env var → Service DNS — that
you'll reuse on EKS.

> **Running Postgres as a pod is a learning exercise, not a production pattern.** You'd
> own backups, failover, patching, and storage. RDS exists precisely so you don't. The
> value here is that the *wiring* is identical, so the app never learns the difference.

```bash
# 1. Build the image (the tag must match the manifests)
docker build -t realtime-app:0.2.0 .

# 2. Postgres: Secret + PVC + Deployment + Service
kubectl apply -f k8s/postgres.yaml
kubectl wait --for=condition=ready pod -l app=postgres --timeout=120s

# 3. Create the schema — one-shot Job
kubectl apply -f k8s/migration-job.yaml
kubectl logs job/db-migrate          # should end: Running upgrade -> 0001

# 4. The app
kubectl apply -f k8s/deployment.yaml -f k8s/service.yaml
kubectl get pods -w                  # wait for READY 1/1
```

Verify:

```bash
curl http://localhost:8080/health/ready
curl -X POST http://localhost:8080/messages \
  -H "Content-Type: application/json" -d '{"body":"from k8s"}'
curl http://localhost:8080/messages
```

Rerunning the migration (Jobs are immutable — you must delete before re-applying):

```bash
kubectl delete job db-migrate --ignore-not-found
kubectl apply -f k8s/migration-job.yaml
```

psql against the in-cluster database:

```bash
kubectl exec -it deploy/postgres -- psql -U realtime -d realtime -c "\d messages"

# or attach a GUI client from Windows:
kubectl port-forward svc/postgres 5432:5432
```

### Why these manifests look like they do

**The Postgres Service is `ClusterIP`, not `LoadBalancer`.** A database has no business
being reachable from outside the cluster; only the app pods need it. Contrast with the
`realtime-app` Service, which is deliberately `LoadBalancer`. Use `port-forward` when
*you* need to reach it — that's a dev tool, not an access mechanism.

**`strategy: Recreate` on the Postgres Deployment.** The default `RollingUpdate` would
start a second Postgres pod before killing the first, and both would try to mount the
same `ReadWriteOnce` volume. The new pod hangs forever and the rollout stalls. Kill the
old one first.

**`PGDATA` points at a *subdirectory*** (`/var/lib/postgresql/data/pgdata`). A freshly
provisioned PVC arrives containing a `lost+found` directory, and `initdb` refuses to
initialise a non-empty directory. This is the standard fix for that exact error.

**A migration Job, not an initContainer.** An initContainer runs on *every* pod, so
scaling to 3 replicas means three concurrent `alembic upgrade` runs racing each other. A
Job runs exactly once. (Alembic does take a lock, so the race is survivable — but
"survivable" is a poor foundation for schema changes.)

**Liveness does not check the database; readiness does.** This is the most important
probe decision in the file:

```
/health        → liveness   → no DB check
/health/ready  → readiness  → SELECT 1
```

If *liveness* checked Postgres, a database blip would make Kubernetes kill and restart
every app pod — which cannot fix a database problem and only makes it worse. Readiness
returning 503 instead pulls the pod out of the Service's endpoints (no traffic) without
killing it, and it rejoins automatically when Postgres recovers. This is also why the app
needs no `wait-for-it.sh`: it may start before the database and simply won't receive
traffic until the database answers.

Verified behaviour — stop Postgres and the app stays alive but stops taking traffic:

```
db stopped:    /health → 200      /health/ready → 503
db restarted:  /health → 200      /health/ready → 200   (data intact)
```

### The commit-a-Secret caveat

[`k8s/postgres.yaml`](k8s/postgres.yaml) contains a Secret with the password in
`stringData`, committed to git on purpose so the local setup is reproducible.

**`stringData` is base64-encoded by Kubernetes, and base64 is encoding, not encryption.**
Anyone with read access to the namespace can decode it. These are throwaway local
credentials. **On EKS you do not commit the Secret** — see below.

---

## 3. AWS — EKS + RDS

What actually changes. Less than you'd expect.

| Concern | Local Kubernetes | EKS |
|---------|-----------------|-----|
| Postgres | `k8s/postgres.yaml` (a pod) | **delete that file** — provision RDS instead |
| `DATABASE_URL` host | `postgres` (Service name) | the RDS endpoint |
| `DB_SSL` | `false` | **`true`** — RDS refuses plaintext |
| Secret | committed, `stringData` | from AWS Secrets Manager, **never committed** |
| Image | local Docker daemon, `IfNotPresent` | pushed to ECR, `imagePullPolicy: Always` |
| Migration Job | same file | **same file, unchanged** |
| `deployment.yaml` | — | **unchanged** |
| `service.yaml` | — | unchanged (real ELB instead of `localhost`) |

That `deployment.yaml` is unchanged is the whole payoff. It reads `DATABASE_URL` from a
Secret by name; it does not care what's in it.

### RDS setup

Create the instance in the **same VPC** as the EKS cluster, in **private subnets** — an
RDS instance should never be publicly accessible. Then the security groups:

```
EKS node security group  --(TCP 5432)-->  RDS security group
```

The RDS security group's inbound rule should reference the **node group's security group
ID**, not a CIDR block. Get this wrong and the symptom is a connection that hangs and
then times out — not a refusal. A hang almost always means security groups; a refusal
means the endpoint or port is wrong.

### The Secret, properly

Store the URL in AWS Secrets Manager, then sync it into the cluster with the **External
Secrets Operator** (or the Secrets Store CSI driver). The app still just reads a
Kubernetes Secret called `postgres-credentials` with a key `DATABASE_URL` — identical to
local. Only its *source* changes.

```yaml
apiVersion: external-secrets.io/v1beta1
kind: ExternalSecret
metadata:
  name: postgres-credentials
spec:
  refreshInterval: 1h
  secretStoreRef:
    name: aws-secrets-manager
    kind: SecretStore
  target:
    name: postgres-credentials     # <-- the name deployment.yaml already expects
  data:
    - secretKey: DATABASE_URL
      remoteRef:
        key: prod/realtime-app/database-url
```

Grant the pod access with **IRSA** (IAM Roles for Service Accounts) — not static AWS keys
in env vars.

### SSL — the asyncpg trap

RDS requires TLS. Everyone's first instinct is:

```
postgresql+asyncpg://user:pass@host:5432/db?sslmode=require    # WRONG
```

**`sslmode` is a libpq/psycopg2 parameter. asyncpg does not understand it** and will
either ignore it or error. asyncpg needs a real `ssl.SSLContext` passed through
`connect_args`. That's what `DB_SSL=true` does in [`app/db.py`](app/db.py):

```python
def build_connect_args() -> dict:
    if not settings.db_ssl:
        return {}
    return {"ssl": ssl.create_default_context()}
```

`build_connect_args()` is imported by [`alembic/env.py`](alembic/env.py) too — migrations
must reach RDS over TLS exactly like the app does. For certificate *verification* against
the AWS CA, download the RDS bundle and build the context from it
(`ssl.create_default_context(cafile="global-bundle.pem")`) rather than the system store.

### Connection pools vs `max_connections`

Each pod holds its **own** pool. The real connection count is:

```
(db_pool_size + db_max_overflow) x replicas
     5        +       10          x   3      = 45 connections
```

RDS caps `max_connections` by instance size — a `t3.micro` allows roughly **87**. Scale
to 10 replicas with the defaults and you exhaust it, and the failure looks like random
`FATAL: too many connections` under load, not a clean error. Do this multiplication
*before* scaling. If pods outgrow it, put **RDS Proxy** in front and point `DATABASE_URL`
at the proxy endpoint — again, a URL change and nothing else.

`pool_pre_ping=True` and `pool_recycle=1800` in [`app/db.py`](app/db.py) exist for RDS
specifically: RDS drops idle connections, and after a failover the pool is full of dead
sockets. Pre-ping turns what would be a hard 500 into a transparent reconnect.

### Migrations on EKS

The same Job, run by CI **before** the app rollout:

```bash
kubectl delete job db-migrate --ignore-not-found
kubectl apply -f k8s/migration-job.yaml
kubectl wait --for=condition=complete job/db-migrate --timeout=300s
kubectl set image deployment/realtime-app realtime-app=<ecr-repo>:0.2.0
```

The Job uses the **same image tag** as the Deployment, always. That is the point: the
schema and the code that assumes it ship as one artifact and cannot drift apart.

To review the SQL before it touches production:

```bash
alembic upgrade head --sql        # prints the SQL, executes nothing
```

---

## Writing migrations that are safe in production

The local-vs-production gap that actually bites.

**A migration and a deploy are not atomic.** During a rollout, old pods and new pods
serve *simultaneously* against one database. A migration that drops or renames a column
breaks the old pods still selecting it.

This forces **expand/contract**. To rename a column:

1. Migrate: add the new column (old code unaffected).
2. Deploy: code writes to both columns.
3. Backfill the new column.
4. Deploy: code reads only the new column.
5. *Later release:* migrate to drop the old column.

Four deploys to rename a column. That isn't Alembic being awkward — it's what
zero-downtime costs, and every migration tool has the same constraint.

**Locks.** Some `ALTER TABLE` statements take an `ACCESS EXCLUSIVE` lock. Adding an index
normally blocks writes for the duration — on a large table, that's an outage. Use
`CREATE INDEX CONCURRENTLY` (Alembic supports it, but the migration must be marked
non-transactional). A migration that's instant against your empty local `messages` table
can lock a 50-million-row production table for minutes.

**`downgrade()` is largely a fiction.** Nobody rolls a schema back in production — the
down-migration for "drop a column" cannot restore the data it deleted. Real recovery is
roll *forward* with a fix, or restore from backup. Keep `downgrade()` for local
iteration; don't treat it as a safety net.

**`--autogenerate` is a draft, not an oracle.** It misses constraint renames, some type
changes, and anything involving data rather than structure — and occasionally proposes
something destructive. Always read the generated file before committing it.

```bash
alembic revision --autogenerate -m "add read flag to messages"
# now OPEN the file and read it
alembic upgrade head
```

---

## Troubleshooting

**`relation "messages" does not exist`**
You never ran the migration. `alembic upgrade head` (Compose) or apply the Job (k8s).

**`sslmode is an invalid keyword argument`**
You put `?sslmode=require` in the URL. asyncpg doesn't speak it — set `DB_SSL=true` instead.

**`InvalidPasswordError` / `password authentication failed`**
The Secret and the Postgres pod disagree. Changing `POSTGRES_PASSWORD` does **not** change
the password of an *already initialised* data directory — the env var only applies on first
`initdb`. Delete the PVC and let it re-init:
`kubectl delete pvc postgres-data` (destroys the data).

**Connection hangs, then times out (EKS)**
Security groups. The RDS SG must allow inbound 5432 from the EKS node SG. A hang means
"nothing is listening / nothing let me through"; a *refusal* means wrong endpoint or port.

**`FATAL: too many connections`**
`(pool_size + max_overflow) x replicas` exceeded the instance's `max_connections`. Shrink
the pool, shrink the replica count, upsize the instance, or put RDS Proxy in front.

**Postgres pod stuck in `CrashLoopBackOff`, logs mention `initdb: directory not empty`**
`PGDATA` is pointing at the volume root instead of a subdirectory. See the note above.

**App pod `READY 0/1` but not restarting**
Working as designed. The readiness probe is failing (no database) while liveness passes.
Check `kubectl logs -l app=realtime-app` and `curl` the pod's `/health/ready`.

---

## Command reference

```bash
# Compose
docker compose up --build -d
docker compose run --rm api alembic upgrade head
docker compose exec db psql -U realtime -d realtime
docker compose down -v                       # wipe including data

# Kubernetes
docker build -t realtime-app:0.2.0 .
kubectl apply -f k8s/postgres.yaml
kubectl apply -f k8s/migration-job.yaml      # delete the old Job first
kubectl apply -f k8s/deployment.yaml -f k8s/service.yaml
kubectl logs job/db-migrate
kubectl exec -it deploy/postgres -- psql -U realtime -d realtime
kubectl port-forward svc/postgres 5432:5432

# Alembic
alembic revision --autogenerate -m "message"
alembic upgrade head
alembic downgrade -1
alembic current                              # what revision is the DB at?
alembic history --verbose
alembic upgrade head --sql                   # print SQL, execute nothing

# Teardown
kubectl delete -f k8s/                       # includes Postgres
kubectl delete pvc postgres-data             # the data outlives the Deployment
```
