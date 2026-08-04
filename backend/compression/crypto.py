import hashlib
import json


def get_sha256(data: bytes | str) -> str:
    if isinstance(data, str):
        data = data.encode("utf-8")
    return hashlib.sha256(data).hexdigest()


def normalize_and_encode(payload: dict) -> list:
    states = []
    for k, v in sorted(payload.items()):
        val_str = json.dumps(v, sort_keys=True)
        states.append(f"STATE_TRANSITION|{k}|{val_str}")
    if not states:
        states = ["STATE_TRANSITION|empty|null"]
    return states


def generate_merkle_chain(states: list) -> tuple[str, list[str]]:
    hashes = []
    prev_hash = ""
    for i, state in enumerate(states):
        h = get_sha256(state if i == 0 else prev_hash + state)
        hashes.append(h)
        prev_hash = h
    return hashes[-1], hashes
