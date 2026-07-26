# Redis — a shared cache across pods

Why the in-process caches (`lru_cache`, `TTLCache`) aren't enough once you run more than
one replica, how Redis fixes it, exactly **where** it plugs into a FastAPI app, and how to
run it locally, in Kubernetes, and on AWS.

Code: [`app/redis_cache.py`](app/redis_cache.py) (the client), [`app/routers/messages.py`](app/routers/messages.py)
(where it's used).

---

## 1. The problem: per-process caches don't scale horizontally

[`CACHE.md`](CACHE.md) built two in-process caches. Both live in **one Python process's
memory**:

```
                 Pod A                          Pod B
        ┌─────────────────────┐        ┌─────────────────────┐
        │ lru_cache / TTLCache │        │ lru_cache / TTLCache │   ← two SEPARATE caches
        └─────────────────────┘        └─────────────────────┘
```

With two replicas behind a Service, requests land on either pod. Consequences:

- **Inconsistency.** A write on pod A invalidates *pod A's* cache. Pod B never hears about
  it and keeps serving its stale copy until its own TTL lapses. Users see different data
  depending on which pod they hit.
- **Wasted warmups.** Every pod fills its cache independently — the same DB query runs once
  per pod instead of once total.
- **No cross-pod invalidation.** There is simply no way for pod A to reach into pod B's
  memory.

For immutable data (the per-date files) this is harmless — every pod computes the same
answer. For **mutable** data (a list that changes on writes) it's a real bug.

## 2. The fix: one cache every pod shares

Redis is a **separate service**. Every pod opens a connection to it, so there is **one
cache**, and a write from any pod is visible to reads from every pod:

```
        Pod A ──┐                       ┌── invalidate on write
        Pod B ──┼──────►  Redis  ◄──────┤   read-through on GET
        Pod C ──┘        (one cache)    └── all pods see the same entries
```

That's the entire reason to introduce Redis here. It trades a memory lookup (nanoseconds,
per-pod, inconsistent) for a network round-trip to Redis (sub-millisecond, shared,
consistent) — worth it the moment correctness across replicas matters.

---

## 3. Where it goes: read-through + invalidate-on-write

The canonical pattern, and the one implemented on `/messages`:

```
GET /messages
   ├─ Redis GET "messages:list:limit=20"
   │     ├─ HIT  → return it (DB untouched)
   │     └─ MISS → query DB → Redis SET (with TTL) → return
   │
POST /messages
   └─ INSERT into DB → commit → Redis DELETE "messages:list:*"  (invalidate)
```

Two rules that are easy to get wrong:

**Invalidate AFTER the DB commit, not before.** If you delete the cache first and a read
sneaks in before the write commits, it re-caches the *old* rows and you're stale again.
Commit is the source of truth; invalidate once it's durable. See
[`create_message`](app/routers/messages.py).

**Cache the serialised form.** We store JSON (datetime already turned into an ISO string),
so a cache hit needs no re-serialisation and the value is language-agnostic in Redis.

### The `where` in one sentence

The cache wraps the **expensive, cacheable read** — here the DB query in `list_messages`.
It lives in the router/service layer, around the data access, never in the HTTP layer and
never around non-idempotent work.

---

## 4. The non-negotiable rule: Redis is an optimization, not a dependency

Every Redis call in [`app/redis_cache.py`](app/redis_cache.py) is wrapped so a Redis outage **degrades
to a cache miss** instead of failing the request:

```python
async def cache_get_json(key):
    try:
        raw = await get_client().get(key)
    except RedisError as exc:
        logger.warning(...)   # log and…
        return None           # …behave exactly like a miss → caller hits the DB
```

- A **read** that can't reach Redis falls through to the database. Slower, still correct.
- A **write** to the cache that fails is logged and ignored — it must never fail the
  request that produced the data.
- Startup **pings** Redis but only **warns** if it's down ([`main.py`](app/main.py)) — the
  app boots and serves regardless.

A cache that can take your whole app down is worse than no cache. This is the property that
makes it safe to add.

---

## 5. The client — a few FastAPI-specific choices

[`app/redis_cache.py`](app/redis_cache.py):

- **`redis.asyncio`, not the sync client.** FastAPI endpoints are async; the async Redis
  client is non-blocking, so it fits directly on the event loop — no threadpool (contrast
  the file caches, which are sync and use FastAPI's threadpool).
- **One client per process, created lazily.** The client owns a connection pool and is
  reused across all requests. Opening a connection per request would erase the benefit.
- **`decode_responses=True`.** Redis returns `str` instead of `bytes`, so `json.loads`
  works directly.
- **`json.dumps(value, default=str)`.** `default=str` serialises `datetime` and friends
  without a custom encoder.
- Closed on shutdown via the lifespan (`await redis_cache.close()`).

---

## 6. Invalidation strategies (the interview follow-up)

We use `DELETE "messages:list:*"` via `scan_iter`. Know the trade-offs:

| Strategy | How | When |
|----------|-----|------|
| **TTL only** | set an expiry, let it lapse | staleness up to the TTL is acceptable; simplest |
| **Explicit delete** (ours) | `DELETE` the affected keys on write | need immediate consistency after a write |
| **Pattern delete** (ours, `scan_iter`) | delete every `prefix:*` key | a write invalidates a whole family of keys |
| **Version bump** | keep `messages:ver`; put it in the key (`messages:list:{ver}:...`); `INCR` on write | huge keyspaces where scanning for a pattern is too slow — one `INCR` orphans all old keys, which then expire |

`scan_iter` is cursor-based and won't block Redis the way the old `KEYS` command does, but
for **millions** of keys the version-bump approach is better: it invalidates in O(1) instead
of scanning. For this app's keyspace, pattern delete is fine.

---

## 7. Running it

### Local — Docker Compose

Redis is a service in [`docker-compose.yml`](docker-compose.yml); the api gets
`REDIS_URL=redis://redis:6379/0` (compose-DNS service name, same idea as `DB_HOST=db`).

```bash
docker compose up -d --build
# watch the cache work:
docker compose logs -f api | grep -i redis
```

Inspect the cache directly:

```bash
docker compose exec redis redis-cli
> KEYS messages:*
> GET "messages:list:limit=20"
> TTL "messages:list:limit=20"
```

### Local — Kubernetes

Redis is in the **local overlay only** ([`k8s/overlays/local/redis.yaml`](k8s/overlays/local/redis.yaml)),
exactly like Postgres. `REDIS_URL` comes from the overlay's ConfigMap.

```bash
kubectl apply -k k8s/overlays/local
kubectl get pods -l app=redis
kubectl exec -it deploy/redis -- redis-cli KEYS 'messages:*'
```

**No PersistentVolumeClaim** on the Redis pod — a cache is disposable. If it restarts and
loses everything, the app repopulates from Postgres on the next miss. Persisting a cache
would be storing what you can always recompute.

### AWS — ElastiCache

You do **not** run your own Redis on EKS, for the same reasons you use RDS over a Postgres
pod: backups, failover, patching, scaling are AWS's job. So:

- **Delete `redis.yaml` from your mental model** on AWS — it's local-only. Provision an
  **ElastiCache for Redis** cluster in the same VPC, private subnets.
- Security group: allow inbound **6379** from the EKS node security group (same pattern as
  RDS — a *hang* means SG, a *refusal* means wrong endpoint).
- Point `REDIS_URL` at the ElastiCache primary endpoint. The dev/uat/prod overlays already
  carry a placeholder `REDIS_URL=redis://<elasticache-endpoint>:6379/0` in their ConfigMap —
  fill it in.
- For TLS/auth (ElastiCache in-transit encryption), use a `rediss://` URL and put the auth
  token in the Secret, not the ConfigMap.

The app code doesn't change at all between local Redis and ElastiCache — only `REDIS_URL`.
Same single-seam design as the database.

---

## 8. Caveats worth stating

- **Per-pod cache vs shared cache is now solved**, but Redis itself is a single point — run
  it HA (ElastiCache multi-AZ / replication) for production, and keep the graceful
  degradation so a Redis blip is a slowdown, not an outage.
- **Cache stampede.** When a hot key expires, many pods can miss simultaneously and all hit
  the DB at once. For truly hot keys, add jittered TTLs or a short lock ("only one pod
  refills"). Not implemented here; name it if asked.
- **Memory + eviction.** A real Redis needs a `maxmemory` and an eviction policy
  (`allkeys-lru` is typical for a pure cache) so it never OOMs. ElastiCache node size sets
  this; for the local pod it's left at defaults.
- **Serialization coupling.** We cache JSON keyed by a version-less key. If `MessageRead`'s
  shape changes, old cached entries could mismatch — bump a key prefix on a breaking change,
  or rely on the short TTL to age them out.

---

## 9. The 60-second interview summary

> "In-process caches like `lru_cache` live in one pod's memory, so with multiple replicas
> they drift — a write on one pod can't invalidate another pod's copy. I moved the mutable
> data (the message list) to Redis, which every pod shares, so there's one cache and writes
> are visible everywhere. The endpoint is read-through: GET checks Redis, on a miss it
> queries Postgres and populates the cache with a TTL; POST commits then invalidates the
> cached list — commit first, so a concurrent read can't re-cache stale rows. Crucially,
> every Redis call degrades to a miss on error, so a Redis outage slows the app down instead
> of taking it out. Locally Redis is a container/pod; on AWS it's ElastiCache, and the only
> thing that changes is the `REDIS_URL`."

---

## Configuration

| Env var | Default | Meaning |
|---------|---------|---------|
| `REDIS_URL` | `redis://localhost:6379/0` | Connection URL. `redis://host:port/db`, or `rediss://` for TLS. |
| `CACHE_TTL_SECONDS` | `60` | Default expiry for cached values. |

Per environment: `redis://redis:6379/0` (Compose & k8s Service name),
`redis://<elasticache-endpoint>:6379/0` (AWS). See [`config.py`](app/config.py).
