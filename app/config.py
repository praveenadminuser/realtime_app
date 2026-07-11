"""Application settings, read from the environment.

The whole local-vs-AWS story lives in one variable: DATABASE_URL. Nothing in the
app knows whether Postgres is a container next door or an RDS instance in a VPC.
Docker Compose sets it, a Kubernetes Secret sets it, and on EKS that same Secret
holds the RDS endpoint instead. No code changes, no `if ENV == "prod"` branches.
"""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # postgresql+asyncpg://user:password@host:5432/dbname
    # The "+asyncpg" part picks the async driver — a plain "postgresql://" URL
    # will fail at startup with SQLAlchemy's async engine.
    database_url: str

    # RDS requires TLS; a local container does not. asyncpg does NOT understand
    # the "?sslmode=require" query parameter that psycopg2 users are used to —
    # it needs an ssl context passed via connect_args. See db.py.
    db_ssl: bool = False

    # Pool sizing. Each pod holds its own pool, so the real connection count is
    # (pool_size + max_overflow) x replicas. RDS instances have a hard
    # max_connections limit — a t3.micro allows only ~87. Worth doing that
    # multiplication before scaling replicas up.
    db_pool_size: int = 5
    db_max_overflow: int = 10

    # Log every SQL statement. Useful locally, far too noisy in a cluster.
    db_echo: bool = False


settings = Settings()