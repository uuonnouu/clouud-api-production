import json
import mimetypes
from typing import Any


def detect_file_type(filename: str, content: bytes) -> str:
    mime_type, _ = mimetypes.guess_type(filename)
    if mime_type:
        return mime_type
    if content.startswith(b"{") or content.startswith(b"["):
        return "application/json"
    try:
        content.decode("utf-8")
        return "text/plain"
    except UnicodeDecodeError:
        return "application/octet-stream"


def analyze_content(content: bytes, file_type: str) -> dict[str, Any]:
    analysis: dict[str, Any] = {
        "detected_type": file_type,
        "original_size": len(content),
        "is_text": False,
        "structure": None,
        "summary": {},
    }
    if file_type == "application/json":
        try:
            document = json.loads(content.decode("utf-8"))
            analysis["is_text"] = True
            if isinstance(document, dict):
                analysis["structure"] = "object"
                analysis["summary"] = {
                    "keys": sorted(document.keys()),
                    "field_count": len(document),
                }
            elif isinstance(document, list):
                analysis["structure"] = "array"
                analysis["summary"] = {
                    "element_count": len(document),
                }
            else:
                analysis["structure"] = type(document).__name__
            analysis["sample"] = document if isinstance(document, (dict, list)) else str(document)
        except Exception:
            analysis["structure"] = "invalid_json"
    else:
        try:
            decoded = content.decode("utf-8")
            analysis["is_text"] = True
            analysis["structure"] = "text"
            analysis["summary"] = {
                "line_count": decoded.count("\n") + 1,
                "word_count": len(decoded.split()),
            }
        except UnicodeDecodeError:
            analysis["structure"] = "binary"
            analysis["summary"] = {
                "magic_prefix": content[:8].hex(),
            }
    return analysis
