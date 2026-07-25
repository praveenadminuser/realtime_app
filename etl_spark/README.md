# Local PySpark ETL — Docker + MinIO

A self-contained playground that runs a real EXTRACT → TRANSFORM → LOAD job against
**MinIO** (an S3-compatible server), so you exercise the exact `s3a://` code path you'd use
on AWS — no AWS account, no cost. Concepts are explained in [`../SPARK_ETL.md`](../SPARK_ETL.md);
this is the how-to-run.

## What's here

```
spark/
  docker-compose.yml     MinIO (fake S3) + bucket seeding + Spark, wired together
  jobs/sample_etl.py     the PySpark job (read CSV → clean → aggregate → write Parquet)
  data/sample_sales.csv  the sample "upstream" file (with a few bad rows on purpose)
```

## Run it

From the `spark/` directory:

```bash
docker compose up --build
```

That does the whole flow in order:

1. **MinIO** starts (the stand-in for S3).
2. **createbuckets** makes `raw` + `curated` buckets and uploads `sample_sales.csv` to
   `raw/sales/` — simulating "upstream drops a file into S3".
3. **Spark** runs `sample_etl.py` in `local[*]` mode: reads the CSV from `s3a://raw/sales/`,
   cleans + aggregates it, and writes partitioned Parquet to `s3a://curated/sales_by_region/`.

The Spark container prints the result and exits. Expected tail:

```
[extract] read 10 well-formed rows from s3a://raw/sales/
[load] wrote 6 aggregated rows to s3a://curated/sales_by_region/
+----------+------+------------+---------+
|txn_date  |region|total_amount|txn_count|
+----------+------+------------+---------+
|2026-07-20|AMER  |150.75      |1        |
|2026-07-20|APAC  |200.5       |2        |
|2026-07-20|EMEA  |200.0       |1        |
|2026-07-21|AMER  |300.0       |1        |
|2026-07-21|APAC  |50.25       |1        |
|2026-07-21|EMEA  |90.0        |1        |
+----------+------+------------+---------+
```

Input has 10 data rows; output has 6 aggregated groups. The bad rows are filtered along the
way: the `amount=not_a_number` value is read as **null** (its `amount > 0` check then drops
it), and the negative-amount and null-region rows are removed by the same filters — so none
of them reach the output. (Aside: on this Spark version `DROPMALFORMED` keeps the
bad-number row with a null field rather than dropping the whole row; the downstream
`amount > 0` filter is what actually removes it. Same result, and a good reminder to verify
bad-record behaviour rather than assume it.)

## See the results

**MinIO console:** http://localhost:9001 (login `minioadmin` / `minioadmin`). Browse the
`curated` bucket → `sales_by_region/` → you'll see `txn_date=2026-07-20/`,
`txn_date=2026-07-21/` folders, each with a Snappy Parquet file. Those folders are
`partitionBy("txn_date")` at work.

**Spark UI:** while the job runs it's at http://localhost:4040 (gone once the job exits — for
a long job you'd watch the DAG, stages, and shuffle here).

## Re-run / reset

```bash
docker compose up                 # re-run (raw already seeded; job overwrites curated)
docker compose down               # stop; keep MinIO data
docker compose down -v            # stop and WIPE MinIO (fresh buckets next time)
```

## How this maps to real AWS

The only thing that changes between here and production is the **connection**, not the job:

| | Local (here) | AWS |
|---|---|---|
| Storage | MinIO container | real S3 |
| `fs.s3a.endpoint` | `http://minio:9000` | *(omit — defaults to AWS)* |
| `path.style.access` | `true` (MinIO needs it) | *(omit)* |
| Credentials | static `minioadmin` keys | **IAM role**, no static keys |
| Runtime / master | `local[*]` | Glue / EMR sets it |

`jobs/sample_etl.py` is the artifact that would run on Glue or EMR unchanged — that's the
whole point of developing against MinIO.

## Troubleshooting

- **`ClassNotFoundException: S3AFileSystem` / no s3a** — the `--packages hadoop-aws` download
  failed (no internet on first run, or a version mismatch). It **must** match Spark's Hadoop
  version: Spark 3.5 → `hadoop-aws:3.3.4`. First run downloads a few hundred MB to
  `/tmp/.ivy2`; subsequent runs are cached.
- **`Connection refused` to minio:9000** — Spark started before MinIO was ready. The
  `depends_on` conditions should prevent it; re-run `docker compose up`.
- **Committer warnings on write** — writing Parquet to S3/MinIO uses a Hadoop committer that
  assumes rename is atomic (S3 has no atomic rename). It works for this sample; the
  **prod job will use the S3A magic committer** — see the TODO in
  [`../SPARK_ETL.md`](../SPARK_ETL.md#next-steps).

## Status

Written and wired, **but not yet run on this machine** — image/jar versions
(`hadoop-aws:3.3.4`) should be confirmed on the first `docker compose up`.
The MinIO ↔ Spark s3a path is the standard local pattern; expect at most a version nudge on
the `--packages` line on the --packages line if versions drift.