import os
import uuid
import hashlib
import json
import time
import asyncio
from datetime import datetime, timezone, timedelta
from fastapi import FastAPI, HTTPException, Depends, Security
from fastapi.security.api_key import APIKeyHeader
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="CLOUUD Local Proof Pipeline API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

MONGO_URL = os.environ.get("MONGO_URL", "mongodb://localhost:27017")
DB_NAME = os.environ.get("DB_NAME", "clouud_db")

client = AsyncIOMotorClient(MONGO_URL)
db = client[DB_NAME]

# API Key Security
API_KEY_NAME = "X-API-Key"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)

async def verify_api_key(api_key: str = Security(api_key_header)):
    if not api_key:
        raise HTTPException(status_code=401, detail="X-API-Key header is missing")
    valid_key = await db.api_keys.find_one({"key": api_key})
    if not valid_key:
        raise HTTPException(status_code=403, detail="Invalid API Key")
    return api_key

# Models
class EventRequest(BaseModel):
    event_type: str = "generic_event"
    payload: dict

class VerifyRequest(BaseModel):
    event_id: str
    proof: dict
    raw_payload: dict = None

class TamperRequest(BaseModel):
    event_id: str
    tampered_payload: dict

class TokenizeRequest(BaseModel):
    event_id: str

def get_sha256(data: str) -> str:
    return hashlib.sha256(data.encode('utf-8')).hexdigest()

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

# --- Background Worker for Data Retention ---
async def retention_worker():
    """Automatically purges raw JSON payloads older than 1 day."""
    while True:
        try:
            one_day_ago = datetime.now(timezone.utc) - timedelta(days=1)
            cutoff_str = one_day_ago.isoformat()
            
            # Find and purge payloads, keeping the proof_blob and event_id intact
            await db.events.update_many(
                {"timestamp": {"$lt": cutoff_str}, "payload": {"$ne": "PURGED"}},
                {"$set": {"payload": "PURGED"}}
            )
        except Exception as e:
            print(f"Retention worker error: {e}")
            
        await asyncio.sleep(3600) # Run every hour

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(retention_worker())
# --------------------------------------------

@app.get("/api/v1/health")
async def health_check():
    return {"status": "ok", "timestamp": datetime.now(timezone.utc).isoformat()}

@app.get("/api/v1/api-keys")
async def create_api_key():
    key = "cld_" + str(uuid.uuid4()).replace("-", "")
    await db.api_keys.insert_one({"key": key, "created_at": datetime.now(timezone.utc).isoformat()})
    return {"api_key": key}

@app.post("/api/v1/transactions")
@app.post("/api/v1/events")
async def ingest_event(req: EventRequest, api_key: str = Depends(verify_api_key)):
    event_id = str(uuid.uuid4())
    doc = {
        "event_id": event_id,
        "event_type": req.event_type,
        "payload": req.payload,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "status": "ingested",
        "proof_blob": None
    }
    await db.events.insert_one(doc)
    return {
        "transaction_id": event_id,
        "event_id": event_id,
        "status": "ingested",
        "timestamp": doc["timestamp"]
    }

@app.post("/api/v1/proof")
async def generate_proof(req: dict, api_key: str = Depends(verify_api_key)):
    event_id = req.get("transaction_id") or req.get("event_id")
    ev = await db.events.find_one({"event_id": event_id}, {"_id": 0})
    if not ev:
        raise HTTPException(status_code=404, detail="Event not found")
        
    if ev.get("payload") == "PURGED":
        raise HTTPException(status_code=400, detail="Cannot generate proof for purged payload")

    start_time = time.time()
    states = normalize_and_encode(ev["payload"])
    root_hash, hashes = generate_merkle_chain(states)
    
    payload_str = json.dumps(ev["payload"])
    original_size = len(payload_str)
    
    proof_blob = {
        "proof_version": "CLOUUD-CORE-1.0",
        "event_id": event_id,
        "algorithm": "CLOUUD_DETERMINISTIC_MERKLE",
        "merkle_root": root_hash,
        "state_count": len(states),
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    compressed_size = len(json.dumps(proof_blob))
    compression_ratio = round(1 - (compressed_size / original_size), 6) if original_size > compressed_size else 0.0
    proof_blob["compression_ratio"] = compression_ratio
    
    await db.events.update_one(
        {"event_id": event_id},
        {"$set": {"proof_blob": proof_blob}}
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
        "processing_time_ms": processing_time_ms
    }

@app.post("/api/v1/tokenize")
async def tokenize_event(req: TokenizeRequest, api_key: str = Depends(verify_api_key)):
    ev = await db.events.find_one({"event_id": req.event_id}, {"_id": 0})
    if not ev or not ev.get("proof_blob"):
        raise HTTPException(status_code=400, detail="Proof must be generated before tokenizing")
        
    token_id = f"CLOUUD-DATA-{get_sha256(req.event_id)[:8].upper()}"
    token_doc = {
        "token_id": token_id,
        "event_id": req.event_id,
        "merkle_root": ev["proof_blob"]["merkle_root"],
        "compression_ratio": ev["proof_blob"]["compression_ratio"],
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.tokens.insert_one(token_doc.copy())
    
    return {
        "status": "minted",
        "token_id": token_id,
        "token_metadata": token_doc
    }

@app.post("/api/v1/verify")
async def verify_proof(req: dict):
    # Verification is public
    start_time = time.time()
    event_id = req.get("transaction_id") or req.get("event_id")
    proof = req.get("proof", {})
    raw_payload = req.get("raw_payload")
    
    ev = await db.events.find_one({"event_id": event_id}, {"_id": 0})
    if not ev:
        return {"valid": False, "reason": "Event not found"}
        
    payload_to_verify = ev.get("payload")
    
    # If the payload has been purged due to retention policy, we MUST rely on the client providing it
    if payload_to_verify == "PURGED":
        if not raw_payload:
            return {"valid": False, "reason": "Payload purged. Provide raw_payload to verify."}
        payload_to_verify = raw_payload
        
    states = normalize_and_encode(payload_to_verify)
    recalculated_root, _ = generate_merkle_chain(states)
    provided_root = proof.get("merkle_root")
    
    is_valid = (recalculated_root == provided_root)
    verification_time_ms = round((time.time() - start_time) * 1000, 2)
    
    return {
        "valid": is_valid,
        "commitment_match": is_valid,
        "recalculated_root": recalculated_root,
        "provided_root": provided_root,
        "verification_time_ms": verification_time_ms
    }

@app.post("/api/v1/tamper")
async def tamper_event(req: TamperRequest):
    res = await db.events.update_one(
        {"event_id": req.event_id, "payload": {"$ne": "PURGED"}},
        {"$set": {"payload": req.tampered_payload}}
    )
    return {"status": "tampered", "modified_count": res.modified_count}

@app.post("/api/v1/admin/trigger-retention")
async def trigger_retention():
    """Forces the retention purge on ALL events for demonstration and testing purposes."""
    res = await db.events.update_many(
        {"payload": {"$ne": "PURGED"}},
        {"$set": {"payload": "PURGED"}}
    )
    return {"status": "success", "purged_count": res.modified_count}
