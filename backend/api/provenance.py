from datetime import datetime, timezone
from typing import Any, Dict, Optional
import uuid

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from .. import core

router = APIRouter()


class ProvenanceRequest(BaseModel):
    engine_id: Optional[str] = None
    skill_id: Optional[str] = None
    source_id: Optional[str] = None
    artifact_id: Optional[str] = None
    package_name: Optional[str] = None
    version: Optional[str] = None
    repository: Optional[str] = None
    branch: Optional[str] = None
    commit_sha: Optional[str] = None
    package_fingerprint: Optional[str] = None
    file_inventory: list[Dict[str, Any]] = Field(default_factory=list)
    source_location: Optional[str] = None
    canonical_registry_reference: Optional[str] = None
    reference_type: str = "uuon_provenance"
    metadata: Dict[str, Any] = Field(default_factory=dict)


@router.post("/provenance")
async def ingest_provenance(
    req: ProvenanceRequest,
    api_key: str = Depends(core.verify_api_key),
) -> dict:
    created_at = datetime.now(timezone.utc)
    event_id = uuid.uuid4().hex
    payload = req.model_dump()
    payload["registration_timestamp"] = created_at.isoformat()
    payload["provenance_status"] = "INGESTED"

    if core.pool is not None:
        await core.pool.execute(
            """
            INSERT INTO events
            (event_id, event_type, payload, timestamp, status, proof_blob, purged)
            VALUES ($1, $2, $3, $4, $5, $6, FALSE)
            """,
            event_id,
            "uuon_provenance",
            payload,
            created_at,
            "provenance_ingested",
            None,
        )

    return {
        "success": True,
        "event_id": event_id,
        "reference_type": req.reference_type,
        "status": "INGESTED",
        "registration_timestamp": created_at.isoformat(),
        "provenance": payload,
    }
