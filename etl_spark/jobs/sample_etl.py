"""Sample PySpark ETL: read CSV from (MinIO) S3, transform, write partitioned Parquet back.

Tiny on purpose, but every step maps to a production concept (see SPARK_ETL.md):
  EXTRACT   explicit schema (no inferSchema) + DROPMALFORMED bad-record handling
  TRANSFORM parse/clean (narrow ops) then groupBy aggregate (a wide op = a real shuffle)
  LOAD      partitioned, Snappy-compressed Parquet

Run via spark-submit inside the spark container — see spark/docker-compose.yml and
spark/README.md. The s3a:// paths point at MinIO locally and would point at real S3
unchanged; only the endpoint/credentials differ.
"""
import os

from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from pyspark.sql.types import DoubleType, StringType, StructField, StructType

RAW_PATH = "s3a://raw/sales/"
CURATED_PATH = "s3a://curated/sales_by_region/"

# Explicit schema — the production default. inferSchema would trigger an extra full pass
# over the data just to guess types; on a huge file that's a wasted read. Declaring the
# schema also means a value that doesn't fit (amount="not_a_number") becomes a MALFORMED
# record we can drop, instead of silently coercing the whole column to string.
SALES_SCHEMA = StructType(
    [
        StructField("txn_date", StringType(), True),  # parsed to a real date in transform
        StructField("region", StringType(), True),
        StructField("product", StringType(), True),
        StructField("amount", DoubleType(), True),
    ]
)


def build_spark() -> SparkSession:
    """SparkSession wired to talk to MinIO (or real S3) over the s3a connector.

    These fs.s3a.* settings are what make s3a:// resolve to MinIO. Against real AWS you drop
    the endpoint + path-style lines and use an IAM role instead of static keys.
    """
    endpoint = os.environ.get("S3_ENDPOINT", "http://minio:9000")
    access_key = os.environ.get("S3_ACCESS_KEY", "minioadmin")
    secret_key = os.environ.get("S3_SECRET_KEY", "minioadmin")

    return (
        SparkSession.builder.appName("sample-sales-etl")
        .config("spark.hadoop.fs.s3a.endpoint", endpoint)
        .config("spark.hadoop.fs.s3a.access.key", access_key)
        .config("spark.hadoop.fs.s3a.secret.key", secret_key)
        # MinIO needs path-style access (bucket in the path, not the hostname).
        .config("spark.hadoop.fs.s3a.path.style.access", "true")
        .config("spark.hadoop.fs.s3a.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem")
        # Default is 200 — absurd for a laptop-sized job; it would write 200 tiny files.
        .config("spark.sql.shuffle.partitions", "8")
        .getOrCreate()
    )


def main() -> None:
    spark = build_spark()
    spark.sparkContext.setLogLevel("WARN")  # quieten the very chatty INFO logs

    # --- EXTRACT ---
    raw = (
        spark.read.option("header", "true")
        # DROPMALFORMED silently drops rows that don't fit the schema (the "not_a_number"
        # amount). Alternatives: PERMISSIVE (default; nulls the bad field) or FAILFAST
        # (crash on the first bad row). A prod job often uses badRecordsPath to QUARANTINE
        # them for inspection rather than dropping silently.
        .option("mode", "DROPMALFORMED")
        .schema(SALES_SCHEMA)
        .csv(RAW_PATH)
    )
    print(f"[extract] read {raw.count()} well-formed rows from {RAW_PATH}")

    # --- TRANSFORM ---
    # Narrow transformations (no shuffle): parse the date, drop junk rows.
    cleaned = (
        raw.withColumn("txn_date", F.to_date("txn_date", "yyyy-MM-dd"))
        .where(F.col("amount") > 0)  # removes the -5.00 row
        .where(F.col("region").isNotNull())  # removes the blank-region row
    )

    # Wide transformation (a SHUFFLE): aggregate per date+region.
    aggregated = cleaned.groupBy("txn_date", "region").agg(
        F.round(F.sum("amount"), 2).alias("total_amount"),
        F.count("*").alias("txn_count"),
    )

    # --- LOAD ---
    # partitionBy writes one folder per txn_date (…/txn_date=2026-07-20/…), so a downstream
    # query filtering on a date reads only that folder (partition pruning). Parquet is
    # Snappy-compressed by default. overwrite makes a re-run idempotent for this dataset.
    (
        aggregated.write.mode("overwrite")
        .partitionBy("txn_date")
        .parquet(CURATED_PATH)
    )

    total = aggregated.count()
    print(f"[load] wrote {total} aggregated rows to {CURATED_PATH}")
    aggregated.orderBy("txn_date", "region").show(truncate=False)

    spark.stop()


if __name__ == "__main__":
    main()