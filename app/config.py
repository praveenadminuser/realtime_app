"""Application settings, read from the environment.

The whole local-vs-cloud story lives in a handful of variables. Nothing in the app
knows whether Postgres is a container next door, an install on your laptop, or an
RDS instance in a VPC — it is handed a host, a port, and credentials, and connects.

Two ways to configure it, in precedence order:

  1. DATABASE_URL — a full URL. If set, it wins and the parts below are ignored.
     Useful when a platform hands you one ready-made (Heroku, Neon, Supabase, CI).

  2. DB_HOST / DB_PORT / DB_USER / DB_PASSWORD / DB_NAME — the parts.
     This is the normal path, and it's the one that matches AWS: Secrets Manager
     stores an RDS credential as exactly these separate fields, so they map 1:1
     with no string-building inside the secret.

Switching environments means changing DB_HOST and DB_SSL. That's it:

    postgres container (compose)  DB_HOST=db                  DB_SSL=false
    postgres container (k8s)      DB_HOST=postgres            DB_SSL=false
    postgres on your laptop       DB_HOST=localhost           DB_SSL=false
      ... same, but app in Docker  DB_HOST=host.docker.internal
    AWS RDS                       DB_HOST=xxx.rds.amazonaws.com  DB_SSL=true
"""
from urllib.parse import quote_plus

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Where do these values actually come from? pydantic-settings resolves each field
    # by walking these sources, HIGHEST PRIORITY FIRST — the first one that has the
    # value wins:
    #
    #   1. arguments passed to Settings(...)        — we never do this
    #   2. real OS environment variables            <-- Docker Compose and Kubernetes land HERE
    #   3. the env_file below (".env")              <-- only ever matters outside a container
    #   4. the field defaults declared in this class
    #
    # Matching is case-insensitive: the env var DB_HOST fills the field db_host.
    #
    # So `env_file=".env"` is a FALLBACK, not the primary source. Concretely:
    #
    #   docker compose up   -> Compose injects DB_HOST etc. as real env vars (level 2),
    #                          which outrank .env. And .env isn't even in the image:
    #                          .dockerignore excludes it. A missing env_file is not an
    #                          error — pydantic just skips it. So the line is a no-op here.
    #   kubectl apply       -> the Secret is injected via envFrom as real env vars (level 2).
    #                          Same story. No .env anywhere.
    #   uvicorn on Windows  -> nothing sets the environment, so .env (level 3) is what
    #                          actually configures the app. THIS is the case it exists for.
    #
    # Confusing overlap worth remembering: Docker Compose ALSO reads a file called .env
    # from the project directory — but only to substitute ${VARIABLES} inside
    # docker-compose.yml before parsing it. It does not pass that file into the container.
    # Same filename, unrelated mechanism, different owner (Docker, not Pydantic).
    #
    # extra="ignore": tolerate unrelated env vars (PATH, HOSTNAME, the dozens Kubernetes
    # injects) instead of raising on every one it doesn't recognise.
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # --- Option 1: a complete URL, overriding everything below ---
    # Must use the "+asyncpg" driver: a plain "postgresql://" URL fails at startup
    # against SQLAlchemy's async engine.
    database_url: str | None = None

    # --- Option 2: the parts (the normal path) ---
    db_host: str = "localhost"
    db_port: int = 5432
    db_user: str = "realtime"
    # SecretStr so the password cannot leak into a log line or a traceback: printing
    # the settings object shows "**********". Read it with .get_secret_value().
    db_password: SecretStr = SecretStr("realtime")
    db_name: str = "realtime"

    # RDS requires TLS; a local container or laptop install does not. Note that
    # asyncpg does NOT understand the "?sslmode=require" query parameter that
    # psycopg2 users reach for — it needs an ssl context via connect_args. See db.py.
    db_ssl: bool = False

    # Pool sizing. Each pod holds its own pool, so the real connection count is
    # (pool_size + max_overflow) x replicas. RDS instances cap max_connections —
    # a t3.micro allows only ~87. Worth doing that multiplication before scaling.
    db_pool_size: int = 5
    db_max_overflow: int = 10

    # Log every SQL statement. Useful locally, far too noisy in a cluster.
    db_echo: bool = False

    # --- JWT / auth ----------------------------------------------------------
    # The key that SIGNS every token. Anyone who has it can mint valid tokens for
    # any user, so it is a top-tier secret: on AWS it belongs in the same Secret as
    # the DB credentials, never committed. The default below is intentionally
    # insecure so local dev works out of the box — main.py logs a loud warning if
    # it's still in use, so it can't quietly reach production.
    jwt_secret: SecretStr = SecretStr("dev-only-insecure-change-me")
    # HS256 = one shared secret signs and verifies (symmetric). Fine when the same
    # service does both. RS256 (a private key signs, a public key verifies) is what
    # you'd move to once OTHER services need to validate tokens without holding the
    # signing key.
    jwt_algorithm: str = "HS256"
    # Short-lived on purpose: a stateless JWT cannot be revoked before it expires,
    # so a leaked token is valid until then. 30 min limits that blast radius. A
    # refresh-token flow (not built yet) is how you keep sessions long without long
    # access tokens.
    access_token_expire_minutes: int = 30

    # --- latest-date file cache ----------------------------------------------
    # Path to a JSON file holding {"latest_date": "yyyymmdd"}. The /latest-date
    # endpoint serves it from an in-memory cache and only re-reads the file when the
    # TTL below expires OR the file's modification time changes. Relative to the
    # working directory (/app in the container, app/ when run locally).
    latest_date_file: str = "data/latest_date.json"
    # How long a cached read stays fresh, in seconds. 300 = 5 minutes.
    latest_date_ttl_seconds: int = 300

    # --- RAG (LangChain + Ollama + Chroma) -----------------------------------
    # Ollama + Chroma run OUTSIDE the app (locally installed, or containers). The app just
    # connects. host.docker.internal reaches host services from inside a container; use
    # localhost when running uvicorn directly on the host. See RAG.md / rag/docker-compose.yml.
    ollama_base_url: str = "http://localhost:11434"
    ollama_llm_model: str = "llama3.2"
    # MUST match between ingest and query — vectors are only comparable if made by the same
    # model. Changing this means re-indexing every document. See RAG.md.
    ollama_embed_model: str = "nomic-embed-text"
    chroma_host: str = "localhost"
    # 8001, NOT 8000: the app itself uses 8000 (uvicorn / the published container port), so
    # Chroma would collide with it on the host — you can't bind one port twice. Run Chroma
    # on 8001: `chroma run --host 0.0.0.0 --port 8001 --path ./chroma-data`.
    chroma_port: int = 8001
    rag_collection: str = "documents"
    rag_chunk_size: int = 1000       # characters per chunk
    rag_chunk_overlap: int = 150     # overlap so a fact split across a boundary isn't lost
    rag_top_k: int = 4               # how many chunks to retrieve into the prompt

    # Directory of per-date content files, one per date: <date_files_dir>/<yyyymmdd>.json.
    # These are IMMUTABLE snapshots (a past date's data doesn't change), so they're cached
    # with functools.lru_cache — no TTL, no mtime check needed. See CACHE.md.
    date_files_dir: str = "data/dates"
    # LRU capacity: the N most-recently-used dates stay in memory, older ones evict. Keeps
    # memory bounded as dates accumulate.
    date_files_cache_size: int = 128

    # --- Redis (SHARED cache across pods) ------------------------------------
    # lru_cache/TTLCache live in one process, so N replicas = N independent caches that
    # drift. Redis is a separate service every pod talks to → one shared cache. See REDIS.md.
    #   local host   redis://localhost:6379/0
    #   compose      redis://redis:6379/0        (the compose service name)
    #   kubernetes   redis://redis:6379/0        (the Service name)
    #   AWS          redis://<elasticache-endpoint>:6379/0
    redis_url: str = "redis://localhost:6379/0"
    # Default TTL for cached values, in seconds.
    cache_ttl_seconds: int = 60

    @property
    def sqlalchemy_url(self) -> str:
        """The URL the engine actually connects with."""
        if self.database_url:
            return self.database_url

        # quote_plus matters. RDS-generated passwords contain characters like @ / : #
        # which are URL syntax — an unescaped '@' in the password splits the URL in
        # the wrong place and you get a baffling "could not translate host name" error
        # naming a fragment of your own password.
        user = quote_plus(self.db_user)
        password = quote_plus(self.db_password.get_secret_value())
        return (
            f"postgresql+asyncpg://{user}:{password}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}"
        )

    @property
    def safe_url(self) -> str:
        """Same thing with the password masked — safe to log."""
        if self.database_url:
            return "<from DATABASE_URL>"
        return f"postgresql+asyncpg://{self.db_user}:***@{self.db_host}:{self.db_port}/{self.db_name}"


settings = Settings()