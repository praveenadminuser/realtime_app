# Caching the latest-date file — problem, solution, trade-offs

A walk-through of the `/latest-date` feature, written so it doubles as an **interview
explanation**: the problem, the naive approach and why it's wrong, the design we chose,
the performance win, and the edge cases an interviewer will probe.

Code: [`services/latest_date_service.py`](app/services/latest_date_service.py),
[`routers/latest_date.py`](app/routers/latest_date.py).

---

## 1. The problem statement

> There is a JSON file on disk, `{"latest_date": "yyyymmdd"}`, that some **external
> process rewrites periodically** (say every few minutes). An API endpoint must return the
> current value. The endpoint is called **often** — many times per second under load.

The tension: the value changes rarely, but the endpoint is hit constantly. So the naive
"read the file on every request" wastes work, and the opposite "read it once at startup"
serves stale data forever. We need something in between.

Two requirements fall out of this:

1. **Freshness** — reflect a file update within a bounded delay (here, 5 minutes), *and*
   pick up a change immediately when the file is actually rewritten.
2. **Efficiency** — don't touch the disk on every request when the value hasn't changed.

---

## 2. The naive approaches, and why each is wrong

**(a) Read + parse the file on every request.**
Correct, but wasteful. Every call pays for a file `open`, `read`, and `json.loads`. At
1,000 req/s that's 1,000 disk reads/s for data that changes once every 5 minutes —
~300,000 identical reads between two real changes. Disk I/O and JSON parsing also add
latency to every response and, on a busy box, contend with everything else.

**(b) Read once at startup, cache forever.**
Fast, but *wrong*: the external process updates the file and the API never notices. It
serves a stale date indefinitely. Fails requirement 1.

**(c) Cache with a fixed TTL only (re-read every 5 min).**
Better — bounds staleness to 5 minutes and collapses 300,000 reads into one. But it has a
blind spot: if the file is rewritten at minute 1, callers keep getting the *old* value
until minute 5. For a "latest date" that may be acceptable; for many use cases a 5-minute
lag on a known-changed file is not.

The design below is (c) **plus** an escape hatch that also catches the change the instant
it happens.

---

## 3. The solution: TTL cache + mtime invalidation

Cache the parsed value in memory and re-read the file only when **either** condition holds:

| Condition | Purpose | Handled by |
|-----------|---------|-----------|
| The cached entry is older than the TTL (5 min) | bound worst-case staleness | `cachetools.TTLCache(ttl=300)` — the entry auto-expires |
| The file's modification time changed | catch a real update *immediately* | an `os.stat()` mtime check on every call |

The logic, per request:

```
stat the file            → current_mtime          (one cheap syscall)
look in the cache
  ├─ present AND cached_mtime == current_mtime  → CACHE HIT   (return from memory)
  └─ absent (TTL expired) OR mtime differs       → CACHE MISS  (re-read + parse + store)
```

So the **common path is a single `stat()`** — no file open, no read, no JSON parse. The
expensive path (open + read + `json.loads`) runs only when the TTL lapses or the file
genuinely changed.

Why `stat()` is the right probe: it returns the file's metadata (including `st_mtime`)
**without opening or reading the file**. It's one of the cheapest syscalls there is —
microseconds, served from the kernel's inode cache — so doing it on every request is
effectively free compared to reading and parsing.

### Why `TTLCache` at all, if we already check mtime?

The mtime check catches *changes*. The TTL is the **safety net** for the cases mtime can't
see: a filesystem that doesn't update mtime reliably (some network mounts), a value you
want periodically re-validated regardless, or an atomic replace that happens to preserve
mtime. Belt (mtime) and suspenders (TTL). Either one alone has a gap; together they don't.

---

## 4. Two implementation decisions worth defending in an interview

These are the "why did you do it *that* way" follow-ups.

**Sync `def`, not `async def`.** The handler does **blocking** file I/O. FastAPI runs a
sync path operation in a **threadpool**, so the blocking read happens off the event loop
and never stalls other requests. Written `async def`, the same blocking read would run
*on* the single event loop and freeze every concurrent request for its duration. Rule:
blocking I/O with no async library → sync `def` and let the framework offload it. See
[`routers/latest_date.py`](app/routers/latest_date.py).

**A `threading.Lock` around the cache.** Precisely *because* it's a sync endpoint in a
threadpool, several threads can enter simultaneously. `cachetools.TTLCache` is **not
thread-safe** — concurrent mutation can corrupt it or raise. The lock serialises access.
The critical section includes the rare file read, which is fine: reads are small and only
happen on a miss, so contention is negligible. See
[`services/latest_date_service.py`](app/services/latest_date_service.py).

> If the interviewer pushes on lock contention: the lock is held for a `stat()` on the hot
> path (microseconds) and additionally a read+parse on the cold path (rare). Throughput is
> bounded by how fast threads can acquire an uncontended lock and do one `stat()` — far
> above realistic request rates. If it ever mattered, you'd switch to a lock-free read of an
> atomically-swapped reference, or a per-thread cache.

---

## 5. The performance improvement, quantified

Take 1,000 req/s, file changing once per 5 minutes.

| | Naive (read every request) | Cached (TTL + mtime) |
|---|---|---|
| File `open`+`read`+`json.loads` per request | **1** | **0** on hits |
| Expensive reads per 5-min window | ~300,000 | **1** |
| Hot-path cost | open + read + parse | one `stat()` |
| Response latency added | disk + parse | ~microseconds |
| Staleness bound | 0 | ≤ 5 min, **or immediate** on a real change |

The win is turning ~300,000 file reads into **one** per window, replacing the hot path
with a single metadata syscall, while *keeping* immediate freshness on a genuine update via
the mtime check. That last part is the interesting bit — most naive caches trade freshness
for speed; this one keeps both because `stat()` is cheap enough to run every time.

Complexity: cache hit is **O(1)** (a dict lookup + one syscall). Memory is **O(1)** — a
single entry (`maxsize=1`).

---

## 6. Edge cases & how they're handled

- **File missing / corrupt / bad JSON** → the service raises `LatestDateError`, the router
  maps it to **503 Service Unavailable** (an operational problem, not a client error).
- **File deleted after being cached** → the per-request `stat()` fails → `LatestDateError`
  → 503. We don't silently serve a stale value from a file that's gone.
- **Torn read (reader sees a half-written file)** → the external writer should write to a
  temp file and `rename()` it over the target (an **atomic** replace on POSIX). Then a
  reader sees either the whole old file or the whole new one, never a partial one. Worth
  stating even though it's the *writer's* responsibility.
- **Concurrent requests during a miss** → the lock means one thread re-reads and the rest
  wait, then hit the now-warm cache. No thundering herd of simultaneous reads.

---

## 7. The distributed angle (the senior-level follow-up)

This cache is **per-process**. Run the API with multiple Uvicorn workers or multiple
Kubernetes replicas and **each has its own copy**. Consequences:

- Different pods can serve **different values** for up to one TTL window after a change,
  until each independently re-reads. For a "latest date" that's usually fine; name it out
  loud so the interviewer knows you see it.
- If the file is baked into the image, every pod reads an identical file — consistent, but
  updating the value means a redeploy. To make it externally updatable in Kubernetes, mount
  it as a **ConfigMap volume** (or a shared volume a sidecar writes). The kubelet updates
  the projected file on a ConfigMap change, its **mtime changes, and our check re-reads it**
  automatically — the design already handles this.
- If you needed **all** replicas to flip at the same instant, or a value too big/hot for
  per-pod copies, you'd move to a **shared cache (Redis)** — at the cost of a network hop
  and a new dependency. That's the classic trade-off: per-process cache is fastest and
  simplest but eventually-consistent across pods; shared cache is consistent but adds
  latency and infrastructure. For this problem, per-process is the right call.

---

## 8. The 60-second interview summary

> "We had a file that changes every few minutes but an endpoint hit thousands of times a
> second. Reading the file per request wasted ~300k reads between changes; caching forever
> served stale data. So I used an in-memory TTL cache — one entry, 5-minute expiry — which
> collapses those reads to one per window and bounds staleness. To *also* pick up a change
> the moment it happens, I `stat()` the file on every request and compare its mtime; a
> mismatch busts the cache early. `stat()` is a microsecond metadata syscall, so the hot
> path is essentially free. The endpoint is a sync function so FastAPI runs the blocking
> read in a threadpool off the event loop, and a lock guards the non-thread-safe cache. The
> one caveat is it's per-process — across replicas it's eventually consistent within a TTL,
> which is acceptable here; if I needed cross-pod consistency I'd move to Redis."

---

## 9. A second cache, a different tool: `lru_cache` for the per-date files

The endpoint grew: given the latest date, also return that date's **content**, stored in
per-date files `data/dates/<yyyymmdd>.json`. These are cached too — but with
`functools.lru_cache`, **not** the TTL+mtime scheme above. Using a different tool here is
the whole point, and a great interview moment because it shows you match the cache to the
data's behaviour rather than reaching for one hammer.

### Why the data is different

| | `latest_date.json` (pointer) | `<date>.json` (content) |
|---|---|---|
| Does the value for a key change? | **yes** — same file, new value over time | **no** — a past date's data is a write-once snapshot |
| Keyed by | nothing (one file) | the **date string** (a function argument) |
| Needs invalidation? | yes (TTL + mtime) | **no** — immutable |
| Right tool | `TTLCache` + mtime + a lock | **`lru_cache`** |

`lru_cache`'s core assumption is a **pure function**: same argument → same result forever.
`read_date_file("20260721")` fits exactly. `read_latest_date()` does **not** — its answer
changes when the file is rewritten, and `lru_cache` would serve the first value forever.
Same reason, opposite conclusion.

### What `lru_cache` buys us here

- **Keyed + bounded.** `@lru_cache(maxsize=128)` keeps the 128 most-recently-used dates and
  evicts the rest — memory is O(maxsize) even as years of dates accumulate. A plain dict
  would grow unbounded.
- **Thread-safe for free.** It has an internal lock, so — unlike `TTLCache` — no manual
  `threading.Lock`.
- **No invalidation code.** Immutable data → nothing to expire.
- **Free stats.** `.cache_info()` (hits / misses / size) is exposed in the response so you
  can watch hits climb.

### What `maxsize` actually does

`maxsize` is the **maximum number of distinct cached entries** — one entry per unique set of
arguments. For us, one entry per unique date string. It is the knob that turns an unbounded
cache into a bounded one:

- **The cache fills** as new dates are requested: `read("20260721")`, `read("20260720")`, …
  each add one entry.
- **When it's full**, the next *new* date evicts the **L**east-**R**ecently-**U**sed entry —
  the date not touched for the longest time. That's the "LRU" in `lru_cache`. Accessing an
  entry marks it most-recently-used, so hot dates never get evicted.
- **`maxsize` caps memory**, not correctness. Set it too low and you get more misses (entries
  evicted then re-read); too high and you hold more dicts in RAM. It never returns wrong data.

Three values of `maxsize`:

| `maxsize` | Behaviour |
|-----------|-----------|
| `128` (ours) | Up to 128 dates cached; the 129th distinct date evicts the LRU one. |
| `None` | **Unbounded** — never evicts. Dangerous with unbounded keys (dates over years grow forever → memory leak). |
| `0` | Caching **disabled** — every call runs the body. Useful to A/B the cache's value. |

**In our scenario specifically:** the dominant access pattern is "give me the *latest* date",
over and over — so one key is red-hot and the hit rate approaches 100% even with a tiny
`maxsize`. `maxsize=1` would already serve the common case perfectly. We chose **128** purely
for headroom: if the UI or an admin browses several recent dates, those stay cached too,
without any risk of unbounded growth. Sizing rule of thumb: **maxsize ≈ the number of
distinct keys you expect to be "active" at once**, plus a margin — not the total number of
keys that will ever exist.

(Aside: the old advice that `maxsize` should be a power of two is a myth for modern CPython —
any positive int is fine.)

### Watching it work: hit/miss + timing logs

`_read_date_file` wraps the cached loader to log every call's outcome and latency:

```
date_file 20260721 MISS in 0.412 ms (hits=0 misses=1 size=1/128)   ← first call: read disk
date_file 20260721 HIT  in 0.004 ms (hits=1 misses=1 size=1/128)   ← served from memory
```

The MISS pays for the file read + JSON parse; the HIT is a dict lookup — ~100× faster here,
and the gap widens with bigger files. We can't log from *inside* the cached function (its body
doesn't run on a hit), so the wrapper detects the outcome by diffing `cache_info().hits` and
times the call with `time.perf_counter()` — the monotonic high-resolution clock, the correct
one for measuring durations (never `time.time()`, which can jump when the wall clock is
adjusted). See [`services/latest_date_service.py`](app/services/latest_date_service.py).

### The two caveats to say out loud

1. **`lru_cache` has NO invalidation.** If a date file is ever *corrected in place*, the old
   content is served until the process restarts or you call `read_date_file.cache_clear()`.
   This is safe **only** because we treat these files as write-once. If they could change,
   this would need the mtime pattern like the pointer file. "Not modified frequently" (the
   original ask) is a yellow flag — confirm it means *never*, or add invalidation.
2. **It returns the SAME object each call.** Callers must treat the result as read-only;
   mutating it corrupts the shared cached copy. We only serialise it into a response, so
   we're safe — but it's the classic `lru_cache` footgun.

### The two caches chained

`GET /latest-date/data` uses both: the TTL-cached pointer answers *which* date, then the
LRU-cached reader returns *that date's* content.

```
get_latest_date()   →  "20260721"   (TTLCache + mtime: catches the pointer changing)
       │
       ▼
_read_date_file("20260721")  →  {...}   (lru_cache: immutable, keyed, bounded)
```

Each cache is doing what it's good at; neither could do the other's job well.

---

## Configuration

| Env var | Default | Meaning |
|---------|---------|---------|
| `LATEST_DATE_FILE` | `data/latest_date.json` | Path to the pointer JSON (relative to the working dir). |
| `LATEST_DATE_TTL_SECONDS` | `300` | Pointer cache lifetime before a forced re-read. |
| `DATE_FILES_DIR` | `data/dates` | Directory of per-date content files. |
| `DATE_FILES_CACHE_SIZE` | `128` | `lru_cache` capacity for per-date files. |

See [`config.py`](app/config.py). Verify the behaviour:

```bash
curl http://localhost:8000/latest-date     # source: "file"   (first call, cold)
curl http://localhost:8000/latest-date     # source: "cache"  (served from memory)
echo '{"latest_date":"20260722"}' > app/data/latest_date.json
curl http://localhost:8000/latest-date     # source: "file"   (mtime changed → re-read)
```

The `source` field exists precisely to make the cache visible in a demo.
