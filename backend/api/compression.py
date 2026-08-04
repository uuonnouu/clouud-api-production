import os
import uuid
from pathlib import Path
from fastapi import APIRouter, File, UploadFile, HTTPException, Depends
from fastapi.responses import JSONResponse

from ..compression.analyzer import analyze_content, detect_file_type
from ..compression.compressor import compress_bytes
from ..compression.artifact import build_artifact_package, artifact_storage_dir
from ..compression.crypto import get_sha256, normalize_and_encode, generate_merkle_chain
from .. import core

router = APIRouter()


@router.post("/compress")
async def compress_upload(file: UploadFile = File(...), api_key: str = Depends(core.verify_api_key)):
    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Uploaded file is empty")

    file_type = detect_file_type(file.filename or "uploaded.file", content)
    analysis = analyze_content(content, file_type)
    compression = compress_bytes(content)
    artifact_id = str(uuid.uuid4())

    proof_input = {
        "artifact_id": artifact_id,
        "filename": file.filename,
        "original_size": len(content),
        "content_type": file_type,
        "analysis": analysis,
    }
    states = normalize_and_encode(proof_input)
    merkle_root, hashes = generate_merkle_chain(states)
    proof_blob = {
        "proof_version": "CLOUUD-COMPRESSION-1.0",
        "artifact_id": artifact_id,
        "filename": file.filename,
        "original_size": len(content),
        "algorithm": compression["algorithm"],
        "merkle_root": merkle_root,
        "state_count": len(states),
        "created_at": __import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat(),
    }

    artifact_dir = build_artifact_package(
        artifact_id=artifact_id,
        filename=file.filename or "uploaded.file",
        original_data=content,
        compressed_bytes=compression["compressed_bytes"],
        compression_algorithm=compression["algorithm"],
        analysis=analysis,
        proof_blob=proof_blob,
    )

    if core.pool is not None:
        await core.pool.execute(
            "INSERT INTO events (event_id, event_type, payload, timestamp, status, proof_blob, purged) VALUES ($1, $2, $3, $4, $5, $6, FALSE)",
            artifact_id,
            "compress_artifact",
            {
                "filename": file.filename,
                "original_size": len(content),
                "compressed_size": compression["compressed_size"],
                "algorithm": compression["algorithm"],
            },
            __import__("datetime").datetime.now(__import__("datetime").timezone.utc),
            "artifact_created",
            proof_blob,
        )

    return JSONResponse(
        {
            "artifact_id": artifact_id,
            "original_filename": file.filename,
            "original_size": len(content),
            "compressed_size": compression["compressed_size"],
            "compression_ratio": round(1 - compression["compressed_size"] / len(content), 6) if len(content) else 0.0,
            "algorithm": compression["algorithm"],
            "artifact_path": str(artifact_dir),
            "proof": proof_blob,
            "download_url": f"/api/v1/artifacts/{artifact_id}",
        }
    )
