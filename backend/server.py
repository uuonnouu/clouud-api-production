import os
import uuid
import hashlib
import json
import time
import asyncio
from contextlib import asynccontextmanager
from datetime import datetime, timezone, timedelta
from typing import Optional

import asyncpg
from fastapi import FastAPI, HTTPException, Depends, Security
from fastapi.security.api_key import APIKeyHeader
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, model_validator
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://localhost:5432/clouud")
ADMIN_KEY = os.environ.get("ADMIN_KEY", "")
API_KEY_NAME = "X-API-Key"
ADMIN_KEY_NAME = "X-Admin-Key"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)
admin_key_header = APIKeyHeader(name=ADMIN_KEY_NAME, auto_error=False)

pool: Optional[asyncpg.pool.Pool] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global pool
    pool = await asyncpg.create_pool(DATABASE_URL)
    async with pool.acquire() as connection:
        await init_db(connection)
    retention_task = asyncio.create_task(retention_worker())
    try:
        yield
    finally:
        retention_task.cancel()
        if pool is not None:
            await pool.close()


app = FastAPI(title="CLOUUD Local Proof Pipeline API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_sha256(data: str) -> str:
    return hashlib.sha256(data.encode("utf-8")).hexdigest()


def normalize_and_encode(payload: dict) -> list:
    states = []
    for k, v in sorted(payload.items()):
        val_str = json.dumps(v, sort_keys=True)
        states.append(f"STATE_TRANSITION|{k}|{val_str}")
    if not states:
        states = ["STATE_TRANSITION|empty|null"]
    return states


def generate_merkle_chain(states: list):
    hashes = []
    prev_hash = ""
    for i, state in enumerate(states):
        h = get_sha256(state) if i == 0 else get_sha256(prev_hash + state)
        hashes.append(h)
        prev_hash = h
    return hashes[-1], hashes


async def init_db(connection: asyncpg.Connection):
    await connection.execute(
        """
        CREATE TABLE IF NOT EXISTS api_keys (
            key TEXT PRIMARY KEY,
            created_at TIMESTAMPTZ NOT NULL,
            revoked BOOLEAN NOT NULL DEFAULT FALSE
        )
        """
    )
    await connection.execute(
        """
        CREATE TABLE IF NOT EXISTS events (
            event_id TEXT PRIMARY KEY,
            event_type TEXT,
            payload JSONB,
            timestamp TIMESTAMPTZ NOT NULL,
            status TEXT,
            proof_blob JSONB,
            purged BOOLEAN NOT NULL DEFAULT FALSE
        )
        """
    )
    await connection.execute(
        """
        CREATE TABLE IF NOT EXISTS tokens (
            token_id TEXT PRIMARY KEY,
            event_id TEXT REFERENCES events(event_id) ON DELETE CASCADE,
            merkle_root TEXT,
            compression_ratio REAL,
            created_at TIMESTAMPTZ NOT NULL
        )
        """
    )


async def retention_worker() -> None:
    while True:
        try:
            one_day_ago = datetime.now(timezone.utc) - timedelta(days=1)
            await pool.execute(
                "UPDATE events SET payload = NULL, purged = TRUE WHERE timestamp < $1 AND purged = FALSE",
                one_day_ago,
            )
        except Exception as e:
            print(f"Retention worker error: {e}")
        await asyncio.sleep(3600)




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


class EventRequest(BaseModel):
    event_type: str = "generic_event"
    payload: dict


class ProofRequest(BaseModel):
    event_id: Optional[str] = None
    transaction_id: Optional[str] = None

    @model_validator(mode="before")
    def at_least_one_id(cls, values):
        event_id = values.get("event_id") or values.get("transaction_id")
        if not event_id:
            raise ValueError("transaction_id or event_id is required")
        values["event_id"] = event_id
        return values


class VerifyRequest(ProofRequest):
    proof: dict
    raw_payload: Optional[dict] = None


class TamperRequest(BaseModel):
    event_id: str
    tampered_payload: dict


class TokenizeRequest(BaseModel):
    event_id: str


@app.get("/api/v1/health")
async def health_check() -> dict:
    return {"status": "ok", "timestamp": datetime.now(timezone.utc).isoformat()}


@app.get("/api/v1/api-keys")
async def create_api_key(admin_key: str = Depends(verify_admin_key)) -> dict:
    key = "cld_" + str(uuid.uuid4()).replace("-", "")
    created_at = datetime.now(timezone.utc)
    await pool.execute(
        "INSERT INTO api_keys (key, created_at, revoked) VALUES ($1, $2, FALSE)",
        key,
        created_at,
    )
    return {"api_key": key, "created_at": created_at.isoformat()}


@app.post("/api/v1/events")
async def ingest_event(req: EventRequest, api_key: str = Depends(verify_api_key)) -> dict:
    event_id = str(uuid.uuid4())
    created_at = datetime.now(timezone.utc)
    await pool.execute(
        "INSERT INTO events (event_id, event_type, payload, timestamp, status, proof_blob, purged) VALUES ($1, $2, $3, $4, $5, $6, FALSE)",
        event_id,
        req.event_type,
        req.payload,
        created_at,
        "ingested",
        None,
    )
    return {
        "transaction_id": event_id,
        "event_id": event_id,
        "status": "ingested",
        "timestamp": created_at.isoformat(),
    }


@app.post("/api/v1/proof")
async def generate_proof(req: ProofRequest, api_key: str = Depends(verify_api_key)) -> dict:
    event_id = req.event_id
    ev = await pool.fetchrow("SELECT event_id, payload, purged FROM events WHERE event_id = $1", event_id)
    if not ev:
        raise HTTPException(status_code=404, detail="Event not found")
    if ev["purged"]:
        raise HTTPException(status_code=400, detail="Cannot generate proof for purged payload")
    payload = ev["payload"] or {}
    start_time = time.time()
    states = normalize_and_encode(payload)
    root_hash, hashes = generate_merkle_chain(states)
    payload_str = json.dumps(payload, sort_keys=True)
    original_size = len(payload_str)
    proof_blob = {
        "proof_version": "CLOUUD-CORE-1.0",
        "event_id": event_id,
        "algorithm": "CLOUUD_DETERMINISTIC_MERKLE",
        "merkle_root": root_hash,
        "state_count": len(states),
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    compressed_size = len(json.dumps(proof_blob))
    compression_ratio = round(1 - (compressed_size / original_size), 6) if original_size > compressed_size else 0.0
    proof_blob["compression_ratio"] = compression_ratio
    await pool.execute(
        "UPDATE events SET proof_blob = $1 WHERE event_id = $2",
        proof_blob,
        event_id,
    )
    processing_time_ms = round((time.time() - start_time) * 1000, 2)
    return {
        "transaction_id": event_id,
        "event_id": event_id,
        "proof": proof_blob,
        "proof_size": compressed_size,
        "original_size": original_size,
        "compression_ratio": compression_ratio,
        "states": states,
        "hashes": hashes,
        "merkle_root": root_hash,
        "processing_time_ms": processing_time_ms,
    }


@app.post("/api/v1/tokenize")
async def tokenize_event(req: TokenizeRequest, api_key: str = Depends(verify_api_key)) -> dict:
    ev = await pool.fetchrow("SELECT event_id, proof_blob FROM events WHERE event_id = $1", req.event_id)
    if not ev or not ev["proof_blob"]:
        raise HTTPException(status_code=400, detail="Proof must be generated before tokenizing")
    token_id = f"CLOUUD-DATA-{get_sha256(req.event_id)[:8].upper()}"
    token_doc = {
        "token_id": token_id,
        "event_id": req.event_id,
        "merkle_root": ev["proof_blob"]["merkle_root"],
        "compression_ratio": ev["proof_blob"]["compression_ratio"],
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    await pool.execute(
        "INSERT INTO tokens (token_id, event_id, merkle_root, compression_ratio, created_at) VALUES ($1, $2, $3, $4, $5)",
        token_doc["token_id"],
        req.event_id,
        token_doc["merkle_root"],
        token_doc["compression_ratio"],
        datetime.fromisoformat(token_doc["created_at"]),
    )
    return {"status": "minted", "token_id": token_id, "token_metadata": token_doc}


@app.post("/api/v1/verify")
async def verify_proof(req: VerifyRequest) -> dict:
    event_id = req.event_id
    proof = req.proof
    raw_payload = req.raw_payload
    ev = await pool.fetchrow("SELECT event_id, payload, purged FROM events WHERE event_id = $1", event_id)
    if not ev:
        return {"valid": False, "reason": "Event not found"}
    payload_to_verify = ev["payload"]
    if ev["purged"]:
        if not raw_payload:
            return {"valid": False, "reason": "Payload purged. Provide raw_payload to verify."}
        payload_to_verify = raw_payload
    payload_to_verify = payload_to_verify or {}
    start_time = time.time()
    states = normalize_and_encode(payload_to_verify)
    recalculated_root, _ = generate_merkle_chain(states)
    provided_root = proof.get("merkle_root")
    is_valid = recalculated_root == provided_root
    verification_time_ms = round((time.time() - start_time) * 1000, 2)
    return {
        "valid": is_valid,
        "commitment_match": is_valid,
        "recalculated_root": recalculated_root,
        "provided_root": provided_root,
        "verification_time_ms": verification_time_ms,
    }


@app.post("/api/v1/tamper")
async def tamper_event(req: TamperRequest, admin_key: str = Depends(verify_admin_key)) -> dict:
    result = await pool.execute(
        "UPDATE events SET payload = $1, purged = FALSE WHERE event_id = $2 AND purged = FALSE",
        req.tampered_payload,
        req.event_id,
    )
    return {"status": "tampered", "modified_count": 1 if result == "UPDATE 1" else 0}


@app.post("/api/v1/admin/trigger-retention")
async def trigger_retention(admin_key: str = Depends(verify_admin_key)) -> dict:
    result = await pool.execute(
        "UPDATE events SET payload = NULL, purged = TRUE WHERE payload IS NOT NULL AND purged = FALSE"
    )
    return {"status": "success", "result": result}
