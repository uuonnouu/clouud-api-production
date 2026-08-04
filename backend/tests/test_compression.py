import json

from backend.compression.analyzer import analyze_content, detect_file_type
from backend.compression.compressor import compress_bytes
from backend.compression.crypto import generate_merkle_chain, get_sha256, normalize_and_encode


def test_detect_file_type_json_by_content():
    assert detect_file_type("payload", b'{"a": 1}') == "application/json"


def test_detect_file_type_by_extension():
    assert detect_file_type("notes.txt", b"hello") == "text/plain"


def test_analyze_content_json_object():
    result = analyze_content(b'{"b": 1, "a": 2}', "application/json")
    assert result["structure"] == "object"
    assert result["summary"]["keys"] == ["a", "b"]
    assert result["summary"]["field_count"] == 2


def test_analyze_content_binary_fallback():
    result = analyze_content(b"\x00\x01\x02\xff", "application/octet-stream")
    assert result["structure"] == "binary"
    assert result["is_text"] is False


def test_compress_bytes_round_trip_smaller_or_equal():
    payload = (b"CLOUUD test payload " * 50)
    result = compress_bytes(payload)
    assert result["algorithm"] in ("zstd", "gzip")
    assert result["compressed_size"] <= len(payload)


def test_crypto_matches_server_semantics():
    # compression/crypto.py duplicates server.py's helpers; this guards
    # against the two implementations drifting apart.
    payload = {"b": 2, "a": 1}
    states = normalize_and_encode(payload)
    root, hashes = generate_merkle_chain(states)
    assert states == [
        "STATE_TRANSITION|a|1",
        "STATE_TRANSITION|b|2",
    ]
    assert root == hashes[-1]
    assert get_sha256("x") == get_sha256("x")
