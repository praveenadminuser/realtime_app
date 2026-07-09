"""Simple logging setup — writes to both the command line (stdout) and a file.

Containers and Kubernetes/EKS collect logs from stdout, so the stream handler
works locally and in a pod with no changes. The file handler keeps a rolling
local copy in ./logs/app.log.
"""
import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

# Make sure the log directory exists before the file handler opens a file in it.
LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)

# Shared format for both destinations so console and file lines look identical.
formatter = logging.Formatter(
    "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
)

# 1. Console handler → stdout (what `docker logs` / kubectl capture).
stream_handler = logging.StreamHandler(sys.stdout)
stream_handler.setFormatter(formatter)

# 2. File handler → logs/app.log, rotating so it can't grow unbounded.
#    maxBytes=1MB per file, keeping the last 3 rotated files (app.log.1 ... .3).
file_handler = RotatingFileHandler(
    LOG_DIR / "app.log", maxBytes=1_000_000, backupCount=3, encoding="utf-8"
)
file_handler.setFormatter(formatter)

logging.basicConfig(
    level=logging.DEBUG,
    handlers=[stream_handler, file_handler],
)

# Import this in other modules:  from logger import logger
logger = logging.getLogger("realtime_app")
