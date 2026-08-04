import json
import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, File, UploadFile, HTTPException, Depends
from fastapi.responses import JSONResponse

from ..compression.analyzer import analyze_content, detect_file_type
from ..compression.compressor import compress_bytes
from ..compression.artifact import build_artifact_package
from ..compression.crypto import get_sha256
from .. import core

router = APIRouter()


@router.post("/compress")
async def compress_upload(
    file: UploadFile = File(...),
):
    content = await file.read()

    if not content:
        raise HTTPException(
            status_code=400,
            detail="Uploaded file is empty"
        )

    artifact_id = str(uuid.uuid4())

    file_type = detect_file_type(file.filename or "uploaded.file", content)
    analysis = analyze_content(content, file_type)

    compression = compress_bytes(content)

    sha256 = get_sha256(content)

    proof_blob = {
        "artifact_id": artifact_id,
        "sha256": sha256,
        "algorithm": compression["algorithm"]
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
            """
            INSERT INTO events
            (
                event_id,
                event_type,
                payload,
                timestamp,
                status,
                proof_blob,
                purged
            )
            VALUES
            ($1,$2,$3,$4,$5,$6,FALSE)
            """,
            artifact_id,
            "compress_artifact",
            json.dumps({
                "filename": file.filename,
                "original_size": len(content),
                "compressed_size": compression["compressed_size"],
                "algorithm": compression["algorithm"]
            }),
            datetime.now(timezone.utc),
            "artifact_created",
            json.dumps(proof_blob),
        )

    return JSONResponse(
        {
            "success": True,
            "artifact_id": artifact_id,
            "filename": file.filename,
            "original_size": len(content),
            "compressed_size": compression["compressed_size"],
            "algorithm": compression["algorithm"],
            "artifact_path": str(artifact_dir),
            "proof": proof_blob
        }
    )
