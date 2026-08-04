import os
from pathlib import Path
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import FileResponse, JSONResponse

from backend.compression.artifact import artifact_storage_dir, verify_artifact_package
from backend.server import pool, verify_api_key

router = APIRouter()


@router.get("/artifacts/{artifact_id}")
async def download_artifact(artifact_id: str, api_key: str = Depends(verify_api_key)):
    artifact_dir = artifact_storage_dir() / artifact_id
    if not artifact_dir.exists() or not artifact_dir.is_dir():
        raise HTTPException(status_code=404, detail="Artifact not found")
    archive_path = artifact_dir / "data.bin"
    if not archive_path.exists():
        raise HTTPException(status_code=404, detail="Artifact binary not found")
    return FileResponse(archive_path, media_type="application/octet-stream", filename=f"{artifact_id}.bin")


class ArtifactVerifyRequest(JSONResponse):
    pass


@router.post("/artifacts/verify")
async def verify_artifact(artifact_id: str, proof_hash: str, api_key: str = Depends(verify_api_key)):
    artifact_dir = artifact_storage_dir() / artifact_id
    if not artifact_dir.exists() or not artifact_dir.is_dir():
        raise HTTPException(status_code=404, detail="Artifact not found")
    result = verify_artifact_package(artifact_dir, proof_hash)
    return JSONResponse(result)
