import os
import uuid
import hashlib
import asyncio
from datetime import datetime, timezone
from typing import Optional

import asyncpg
from fastapi import HTTPException, Depends
from fastapi.security.api_key import APIKeyHeader
from dotenv import load_dotenv
import logging

load_dotenv()

# Debug logger for local development troubleshooting. Remove or lower level in production.
logger = logging.getLogger("clouud.debug")
logger.setLevel(logging.DEBUG)
if not logger.handlers:
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    formatter = logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s")
    ch.setFormatter(formatter)
    logger.addHandler(ch)

DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://localhost:5432/clouud")
ADMIN_KEY = os.environ.get("ADMIN_KEY", "")
API_KEY_NAME = "X-API-Key"
ADMIN_KEY_NAME = "X-Admin-Key"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)
admin_key_header = APIKeyHeader(name=ADMIN_KEY_NAME, auto_error=False)

pool: Optional[asyncpg.pool.Pool] = None

logger.debug("core module loaded; DATABASE_URL=%s", os.environ.get("DATABASE_URL"))


def get_sha256(data: str) -> str:
    return hashlib.sha256(data.encode("utf-8")).hexdigest()


async def verify_api_key(api_key: str = Depends(api_key_header)) -> str:
    logger.debug("verify_api_key called; incoming X-API-Key header=%r", api_key)
    if not api_key:
        raise HTTPException(status_code=401, detail="X-API-Key header is missing")
    if pool is None:
        logger.error("verify_api_key failed: pool is None (no DB connection)")
        raise HTTPException(status_code=500, detail="Database connection is not available")
    try:
        logger.debug("Using db pool: %r", pool)
        row = await pool.fetchrow("SELECT key, revoked FROM api_keys WHERE key = $1", api_key)
        logger.debug("DB fetchrow result for key %s: %r", api_key, row)
    except Exception as exc:
        logger.exception("Database query error while verifying API key: %s", exc)
        raise HTTPException(status_code=500, detail="DB error during API key verification")
    if not row or row["revoked"]:
        logger.warning("API key lookup failed or revoked for key=%s; row=%r", api_key, row)
        raise HTTPException(status_code=403, detail="Invalid or revoked API Key")
    check_rate_limit(api_key)
    logger.debug("API key validated: %s", api_key)
    return api_key


async def verify_admin_key(admin_key: str = Depends(admin_key_header)) -> str:
    if not ADMIN_KEY:
        raise HTTPException(status_code=500, detail="Admin key is not configured")
    if not admin_key or admin_key != ADMIN_KEY:
        raise HTTPException(status_code=403, detail="Invalid admin key")
    return admin_key

from collections import defaultdict
import time

_request_counts: dict = defaultdict(list)
RATE_LIMIT = 100  # requests per minute per key

def check_rate_limit(api_key: str) -> None:
    now = time.time()
    window = 60
    _request_counts[api_key] = [
        t for t in _request_counts[api_key]
        if now - t < window
    ]
    if len(_request_counts[api_key]) >= RATE_LIMIT:
        raise HTTPException(
            status_code=429,
            detail="Rate limit exceeded. 100 requests per minute."
        )
    _request_counts[api_key].append(now)
