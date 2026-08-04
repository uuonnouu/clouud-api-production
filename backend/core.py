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

load_dotenv()

DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://localhost:5432/clouud")
ADMIN_KEY = os.environ.get("ADMIN_KEY", "")
API_KEY_NAME = "X-API-Key"
ADMIN_KEY_NAME = "X-Admin-Key"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)
admin_key_header = APIKeyHeader(name=ADMIN_KEY_NAME, auto_error=False)

pool: Optional[asyncpg.pool.Pool] = None


def get_sha256(data: str) -> str:
    return hashlib.sha256(data.encode("utf-8")).hexdigest()


async def verify_api_key(api_key: str = Depends(api_key_header)) -> str:
    if not api_key:
        raise HTTPException(status_code=401, detail="X-API-Key header is missing")
    if pool is None:
        raise HTTPException(status_code=500, detail="Database connection is not available")
    row = await pool.fetchrow("SELECT key, revoked FROM api_keys WHERE key = $1", api_key)
    if not row or row["revoked"]:
        raise HTTPException(status_code=403, detail="Invalid or revoked API Key")
    return api_key


async def verify_admin_key(admin_key: str = Depends(admin_key_header)) -> str:
    if not ADMIN_KEY:
        raise HTTPException(status_code=500, detail="Admin key is not configured")
    if not admin_key or admin_key != ADMIN_KEY:
        raise HTTPException(status_code=403, detail="Invalid admin key")
    return admin_key
