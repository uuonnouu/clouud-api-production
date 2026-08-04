import os
import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .crypto import get_sha256

ARTIFACTS_DIR = Path(os.environ.get("CLOUUD_ARTIFACTS_DIR", "./artifacts"))
ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)


def artifact_storage_dir() -> Path:
    return ARTIFACTS_DIR


def build_artifact_package(
    artifact_id: str,
    filename: str,
    original_data: bytes,
    compressed_bytes: bytes,
    compression_algorithm: str,
    analysis: dict[str, Any],
    proof_blob: dict[str, Any],
) -> Path:
    artifact_dir = ARTIFACTS_DIR / artifact_id
    artifact_dir.mkdir(parents=True, exist_ok=True)

    data_path = artifact_dir / "data.bin"
    metadata_path = artifact_dir / "metadata.json"
    proof_path = artifact_dir / "proof.json"

    data_path.write_bytes(compressed_bytes)
    metadata = {
        "artifact_id": artifact_id,
        "original_filename": filename,
        "original_size": len(original_data),
        "compressed_size": len(compressed_bytes),
        "compression_ratio": round(1 - (len(compressed_bytes) / len(original_data)), 6)
        if len(original_data) > 0
        else 0.0,
        "algorithm": compression_algorithm,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "hash": get_sha256(compressed_bytes),
        "analysis": analysis,
    }
    proof_metadata = {
        "proof_hash": get_sha256(json.dumps(proof_blob, sort_keys=True).encode("utf-8")),
        "merkle_root": proof_blob.get("merkle_root"),
        "verification_status": "created",
        "proof_blob": proof_blob,
    }
    metadata_path.write_text(json.dumps(metadata, indent=2))
    proof_path.write_text(json.dumps(proof_metadata, indent=2))
    return artifact_dir


def verify_artifact_package(artifact_dir: Path, proof_hash: str) -> dict[str, Any]:
    metadata_path = artifact_dir / "metadata.json"
    proof_path = artifact_dir / "proof.json"
    if not metadata_path.exists() or not proof_path.exists():
        return {"valid": False, "reason": "Artifact package incomplete"}

    metadata = json.loads(metadata_path.read_text())
    proof_metadata = json.loads(proof_path.read_text())
    expected_hash = proof_metadata.get("proof_hash")
    if expected_hash != proof_hash:
        return {"valid": False, "reason": "Proof hash mismatch"}

    recomputed = get_sha256((proof_metadata.get("proof_blob") or {}).get("merkle_root", "").encode("utf-8"))
    proof_valid = proof_metadata.get("proof_hash") == expected_hash
    return {
        "valid": proof_valid,
        "artifact_id": metadata.get("artifact_id"),
        "verified": proof_valid,
        "compression_verified": metadata.get("hash") == get_sha256((artifact_dir / "data.bin").read_bytes()),
        "proof_hash": proof_hash,
        "expected_proof_hash": expected_hash,
        "metadata": metadata,
        "proof_metadata": proof_metadata,
    }
