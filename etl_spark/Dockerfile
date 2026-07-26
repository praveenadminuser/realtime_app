# A self-contained PySpark runner. We build our own instead of pulling bitnami/apache
# Spark images, because those third-party tags move and disappear (bitnami/spark:3.5
# vanished under Broadcom's 2025 catalog changes). This pins EXACTLY what we run.
#
# pyspark from pip bundles the full Spark distribution (jars + spark-submit), so all we
# add on top of Python is a JRE — Spark's engine is a JVM.
#
# Pinned to -bookworm (Debian 12), NOT plain -slim: newer -slim tracks Debian 13 (Trixie),
# which dropped openjdk-17 for openjdk-21. Spark 3.5 officially supports Java 17 (Java 21 is
# still experimental), so we stay on the distro that ships 17.
FROM python:3.11-slim-bookworm

# Java is required by Spark. headless JRE = no GUI libs, smaller image. procps gives `ps`,
# which some Spark scripts call.
RUN apt-get update \
    && apt-get install -y --no-install-recommends openjdk-17-jre-headless procps \
    && rm -rf /var/lib/apt/lists/*

# Spark 3.5.3 bundles the Hadoop 3.3.4 client, so the hadoop-aws:3.3.4 package the job pulls
# at runtime matches — version alignment is what makes s3a work.
RUN pip install --no-cache-dir pyspark==3.5.3

# `java` is on PATH via the JRE's alternatives symlink, so PySpark's launcher finds it
# without us guessing the arch-specific JAVA_HOME path.
WORKDIR /opt/jobs
