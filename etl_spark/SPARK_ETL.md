# PySpark ETL — basics, architecture, and a local playground

A senior-level explanation of processing huge files with PySpark: the mental model, how it
runs in companies, the efficiency techniques that make it "production-grade", and a local
Docker + MinIO setup that mirrors the real S3 flow with zero AWS cost.

Scope: **this doc explains; [`etl_spark/`](etl_spark/) implements a small end-to-end sample.** A
prod-grade job is a deliberate later step — see [Next steps](#next-steps).

---

## 1. What Spark actually is

Spark is a **distributed compute engine**. You write one Python program (the **driver**);
Spark splits the work across **executors** (JVM processes, possibly on many machines), each
processing a slice of the data in parallel. The unit of parallelism is the **partition** — a
chunk of the dataset. A 500 GB file becomes ~4,000 partitions of ~128 MB, spread across the
cluster. That's the whole idea: big data isn't processed by one machine, it's partitioned
across many.

```
        Driver (your Python)  ── builds a plan (DAG), schedules tasks
             │
   ┌─────────┼─────────┐
   ▼         ▼         ▼
 Executor  Executor  Executor     ← each runs tasks on its partitions, in parallel
   │         │         │
 part 1..N  part ..    part ..
```

Two ideas to state precisely in an interview:

- **Lazy evaluation.** Transformations (`filter`, `select`, `join`, `withColumn`) don't run —
  they build a **DAG** (a plan). Nothing executes until an **action** (`write`, `count`,
  `collect`). Spark optimizes the whole plan at once via the **Catalyst optimizer** before
  running it, and executes with the **Tungsten** engine (off-heap memory, code generation).
- **Narrow vs wide transformations.** Narrow (`filter`, `map`, `withColumn`) stay within a
  partition — cheap. Wide (`groupBy`, `join`, `distinct`, `orderBy`) require a **shuffle** —
  data moves across the network between executors. **Shuffles are the #1 cost.** Most Spark
  tuning is "reduce or optimize shuffles."

**Use the DataFrame/SQL API, not RDDs.** DataFrames go through Catalyst (optimized); raw RDDs
don't. RDDs are legacy for 99% of ETL.

---

## 2. Can you use PySpark outside AWS Glue? Yes — Glue is one runtime among many

Common misconception. **PySpark is the Python API for open-source Apache Spark.** Glue
doesn't own it — Glue is *managed, serverless Spark* plus AWS extras (Data Catalog, crawlers,
job bookmarks). The **same PySpark code** runs in all of these:

| Where | What it is | Trade-off |
|---|---|---|
| **Local** (`local[*]`) | Spark on your laptop, threads as executors | dev/test only |
| **AWS Glue** | serverless Spark; submit a script | zero ops, higher $/hr, some Glue-only APIs |
| **Amazon EMR** | managed Spark cluster on EC2 | cheapest at scale, most ops |
| **EMR Serverless** | serverless Spark, no Glue catalog framing | middle ground |
| **Databricks** | premium managed Spark (Auto Loader, Delta) | best DX, cost |
| **Spark on Kubernetes** | executors as pods (could run on your EKS) | you own the platform |

The senior framing: **your ETL *logic* is portable; only the *runtime* and *I/O connectors*
change.** That portability is exactly why you develop locally and deploy to Glue/EMR
unchanged.

---

## 3. How "file lands in S3 → process it" works in companies

Event-driven. "As soon as the file is available" means S3 emits an event and something
reacts:

```
Upstream ──▶ S3 (raw / landing bucket)
                │  s3:ObjectCreated event
                ▼
        EventBridge  (or S3 → SQS / SNS)
                │
                ▼
     Lambda / Step Functions        ◀── starts the Spark job
                │  StartJobRun
                ▼
     Spark job (Glue / EMR / Databricks)
                │  EXTRACT → TRANSFORM → LOAD
                ▼
   S3 (curated bucket, Parquet)  ──▶ Athena / Redshift / a warehouse
```

Common wirings:
- **Glue:** S3 event → EventBridge rule → **Lambda** calls `glue.start_job_run()`; or
  EventBridge → **Step Functions** for multi-step pipelines with retries.
- **Databricks:** **Auto Loader** watches the S3 prefix and incrementally ingests new files —
  it tracks what's already processed, no Lambda needed.
- **EMR:** EventBridge → Step Functions spins up a **transient cluster**, runs, tears down
  (cheapest for periodic big jobs).

**Zones / medallion convention:** **raw/bronze** (as-landed) → **cleaned/silver** (validated,
typed) → **curated/gold** (business-ready, aggregated). Each stage is a Spark job writing to
the next S3 prefix.

---

## 4. The "huge file" nuance most people miss

A *single* huge file does **not** automatically parallelize. It depends on whether the format
is **splittable** — can Spark hand different byte ranges to different executors?

| Format | Splittable? | Consequence |
|---|---|---|
| CSV/JSON, **uncompressed** | ✅ | split into partitions across executors |
| CSV/JSON + **gzip** | ❌ | the **entire** file is read by **one** core — single-threaded |
| CSV + **bzip2** | ✅ | splittable but slow codec |
| **Parquet / ORC** | ✅ | columnar, splittable, compressed — the right answer |

So "one huge gzipped CSV" is a trap: no matter the cluster size, one core reads it. Senior
moves: ask upstream for **splittable** delivery (many medium files, or Parquet, or
snappy/uncompressed), or land it and immediately `repartition()` after the single-threaded
read to parallelize the rest.

The flip side is the **small files problem**: 100,000 tiny files = one task each = huge
scheduling overhead. Sweet spot: files of **~128 MB–1 GB**.

---

## 5. Production-grade efficiency techniques (the interview checklist)

- **Columnar format + Snappy.** Read/write **Parquet**, not CSV. Enables **column pruning**
  (read only needed columns) and **predicate pushdown** (skip row groups that don't match a
  filter) — often 10–100× less I/O.
- **Explicit schema, never `inferSchema` on huge data.** Inference is a whole extra pass over
  the file. Define a `StructType`.
- **Partition the output** (`.write.partitionBy("date")`) so downstream scans only relevant
  folders. Don't over-partition (→ small files).
- **Broadcast joins** for big×small: `broadcast(small_df)` ships the small table to every
  executor, skipping the shuffle.
- **Handle skew.** If one key holds most rows, one task does all the work (stragglers). Fix
  with **salting** (randomize the key) or lean on **AQE** (Adaptive Query Execution, on by
  default in Spark 3 — auto-coalesces partitions and handles some skew).
- **`repartition()` vs `coalesce()`.** `repartition(n)` reshuffles to exactly n (can
  increase); `coalesce(n)` merges without a full shuffle (decrease only) — use it to avoid
  writing thousands of tiny output files.
- **`cache()`/`persist()` only when a DataFrame is reused** across multiple actions.
- **Partition sizing.** Target ~128 MB/partition; tune `spark.sql.shuffle.partitions`
  (default 200 is wrong for both tiny and huge jobs).
- **Bad-record handling.** `mode="PERMISSIVE"` (default, nulls bad fields), `DROPMALFORMED`,
  or `FAILFAST`; `badRecordsPath` to quarantine. A prod ETL never dies on one bad row.
- **Idempotency / no reprocessing.** Glue **job bookmarks** or Databricks Auto Loader
  checkpoints track processed files. Write to a deterministic partition so a retry overwrites
  instead of duplicating.
- **S3 write committers.** S3 has no atomic rename, so the default Hadoop committer is slow/
  unsafe on S3. Prod uses the **S3A magic committer** or Glue/EMR's optimized committer. (A
  local-sample caveat we'll revisit for the prod job.)
- **Observability.** The **Spark UI** (DAG, stages, shuffle read/write, skew, spills) is where
  you diagnose everything — know how to read it.

---

## 6. Running it locally (Windows) — Docker + MinIO

Two paths; **Docker is strongly recommended on Windows.**

**Docker (recommended).** Spark needs a JVM, and native PySpark on Windows also needs
`winutils.exe`/`HADOOP_HOME` — a notorious time-sink. A container avoids all of it. We pair
Spark with **MinIO**, an **S3-compatible** server in a container, so the code path is
`s3a://…` exactly as against real S3 — only the endpoint differs. You test the real S3 read/
write logic with no AWS account.

```
┌─────────────┐   s3a://raw/…     ┌──────────┐   s3a://curated/…   ┌─────────────┐
│  MinIO      │◀──────────────────│  Spark   │────────────────────▶│  MinIO      │
│ (fake S3)   │   read sample     │ local[*] │   write Parquet     │ (fake S3)   │
└─────────────┘                   └──────────┘                      └─────────────┘
```

**Native pip.** `pip install pyspark` (bundles Spark) + a JDK 17 + `winutils.exe`. Works, but
the Hadoop-on-Windows friction is real — skip it here.

`local[*]` is the master URL: one process, all CPU cores as pseudo-executors. **Your code is
identical to cluster code** — only the master changes (Glue/EMR set it for you). Develop and
test on a 10 MB sample locally; deploy the same script for the 500 GB run.

The concrete setup lives in [`etl_spark/`](etl_spark/) — see [`etl_spark/README.md`](etl_spark/README.md).

---

## 7. The sample job (what [`etl_spark/`](etl_spark/) does)

A minimal but real EXTRACT → TRANSFORM → LOAD, exercising the core concepts:

1. **Extract** — read `s3a://raw/sales/*.csv` from MinIO with an **explicit schema** (no
   `inferSchema`) and **`DROPMALFORMED`** bad-record handling.
2. **Transform** — parse the date, filter out non-positive amounts and null regions, then
   **aggregate** (`groupBy` date+region → sum, count) — a wide transformation, i.e. a real
   shuffle.
3. **Load** — write **partitioned Parquet** (`partitionBy("txn_date")`, Snappy) to
   `s3a://curated/…`.

It's deliberately tiny, but every line maps to a production concept, so it doubles as a
teaching artifact. The prod version below scales these up.

---

## Next steps

- [x] Concepts documented (this file).
- [x] Local Docker + MinIO sample — [`etl_spark/`](etl_spark/).
- [ ] **Prod-grade PySpark ETL** (the real exercise). A scenario that exercises most of §5:
  - larger, **partitioned** input; **Parquet** in/out with pushdown + pruning
  - a **broadcast join** against a dimension table
  - deliberate **data skew** + a **salting** fix, AQE on/off comparison
  - **schema evolution** / bad-record quarantine (`badRecordsPath`)
  - the **S3A magic committer** for correct, fast S3 writes
  - **idempotency** (deterministic partition overwrite) and a re-run that doesn't duplicate
  - reading the **Spark UI** to diagnose a shuffle/skew
  - the **event trigger** (S3 → EventBridge → Lambda → job) sketched for Glue/EMR