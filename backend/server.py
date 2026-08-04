import os
import uuid
import hashlib
import json
import time
from datetime import datetime, timezone
from fastapi import FastAPI, HTTPException
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

# Models
class EventRequest(BaseModel):
    event_type: str = "generic_event"
    payload: dict

class VerifyRequest(BaseModel):
    event_id: str
    proof: dict

class TamperRequest(BaseModel):
    event_id: str
    tampered_payload: dict

def get_sha256(data: str) -> str:
    return hashlib.sha256(data.encode('utf-8')).hexdigest()

def normalize_and_encode(payload: dict) -> list:
    """Deterministically flattens a JSON payload into an array of semantic states."""
    states = []
    # Sort keys to guarantee deterministic order
    for k, v in sorted(payload.items()):
        # In a real engine, this would be a deep structural parse
        val_str = json.dumps(v, sort_keys=True)
        states.append(f"STATE_TRANSITION|{k}|{val_str}")
    if not states:
        states = ["STATE_TRANSITION|empty|null"]
    return states

def generate_merkle_chain(states: list):
    """Generates a sequential hash chain culminating in a root commitment."""
    hashes = []
    prev_hash = ""
    for i, state in enumerate(states):
        h = get_sha256(state) if i == 0 else get_sha256(prev_hash + state)
        hashes.append(h)
        prev_hash = h
    return hashes[-1], hashes

@app.get("/api/v1/health")
async def health_check():
    return {"status": "ok", "timestamp": datetime.now(timezone.utc).isoformat()}

# Accepting both /transactions and /events to support all user curl commands
@app.post("/api/v1/transactions")
@app.post("/api/v1/events")
async def ingest_event(req: EventRequest):
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
        "transaction_id": event_id,  # Returned as transaction_id for curl compatibility
        "event_id": event_id,
        "status": "ingested",
        "timestamp": doc["timestamp"]
    }

@app.post("/api/v1/proof")
async def generate_proof(req: dict):
    # Support both transaction_id and event_id from incoming request
    event_id = req.get("transaction_id") or req.get("event_id")
    ev = await db.events.find_one({"event_id": event_id}, {"_id": 0})
    if not ev:
        raise HTTPException(status_code=404, detail="Event not found")

    start_time = time.time()

    # 1. State Normalization & CLOUUD Encoder
    states = normalize_and_encode(ev["payload"])
    
    # 2. Hash Generation & Merkle Commitment
    root_hash, hashes = generate_merkle_chain(states)
    
    # 3. Compressed Proof Artifact
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

@app.post("/api/v1/verify")
async def verify_proof(req: dict):
    start_time = time.time()
    
    event_id = req.get("transaction_id") or req.get("event_id")
    proof = req.get("proof", {})
    
    ev = await db.events.find_one({"event_id": event_id}, {"_id": 0})
    if not ev:
        return {"valid": False, "reason": "Event not found"}
        
    # The true test of integrity: Re-run the encoder on the CURRENT database payload
    # If the payload was tampered with, the generated root will not match the proof root.
    states = normalize_and_encode(ev["payload"])
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
        {"event_id": req.event_id},
        {"$set": {"payload": req.tampered_payload}}
    )
    return {"status": "tampered", "modified_count": res.modified_count}
