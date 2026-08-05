"""
UUON Plugin OpenAPI 3.1 Manifest
GET /api/v1/plugin/openapi.json  — full OpenAPI 3.1 spec
GET /api/v1/plugin/manifest      — lightweight connector manifest (n8n / Make / MCP compatible)

Any system that accepts OpenAPI 3.1 can import this as a custom connector.
"""

from fastapi import APIRouter
from .registry import ENGINES

router = APIRouter()

BASE_URL = "https://uuon.world"  # override via env in deployment


def _openapi_spec() -> dict:
    paths = {}

    # Engine list
    paths["/api/v1/engines"] = {
        "get": {
            "operationId": "listEngines",
            "summary": "List all registered UUON engines",
            "tags": ["engines"],
            "security": [],
            "responses": {
                "200": {
                    "description": "Engine registry",
                    "content": {"application/json": {"schema": {"type": "object"}}}
                }
            }
        }
    }

    # Per-engine describe + run
    for eid, eng in ENGINES.items():
        describe_path = f"/api/v1/engines/{eid}"
        paths[describe_path] = {
            "get": {
                "operationId": f"describeEngine_{eid.replace('-', '_')}",
                "summary": f"Describe {eng['name']}",
                "tags": ["engines", eid],
                "security": [],
                "responses": {
                    "200": {
                        "description": "Engine schema with input/output terminal definitions",
                        "content": {"application/json": {"schema": {"type": "object"}}}
                    }
                }
            },
            "post": {
                "operationId": f"runEngine_{eid.replace('-', '_')}",
                "summary": f"Run {eng['name']} — Layer {eng['layer']} / {eng['bio']}",
                "description": eng["description"],
                "tags": ["engines", eid],
                "security": [{"apiKey": []}],
                "requestBody": {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "required": ["p_vector"],
                                "properties": {
                                    "p_vector": {
                                        "type": "object",
                                        "description": "Parameter vector — minimal seed encoding engine output",
                                        "properties": {
                                            k: {
                                                "type": v.get("type", "string"),
                                                "default": v.get("default"),
                                                "description": v.get("description", ""),
                                                **({"enum": v["enum"]} if "enum" in v else {}),
                                                **({"minimum": v["min"]} if "min" in v else {}),
                                                **({"maximum": v["max"]} if "max" in v else {}),
                                            }
                                            for k, v in eng["terminal_in"]["schema"].items()
                                        }
                                    },
                                    "output_format": {
                                        "type": "string",
                                        "enum": eng["terminal_out"]["formats"] + ["json"],
                                        "default": "json",
                                    }
                                }
                            }
                        }
                    }
                },
                "responses": {
                    "200": {
                        "description": "Engine output with USAL-1.0 provenance envelope and Merkle proof",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "request_id": {"type": "string"},
                                        "engine_id": {"type": "string"},
                                        "layer": {"type": "integer"},
                                        "bio": {"type": "string"},
                                        "p_vector": {"type": "object"},
                                        "output": {"type": "object"},
                                        "provenance": {"type": "object"},
                                        "proof": {"type": "object"},
                                    }
                                }
                            }
                        }
                    },
                    "401": {"description": "Missing X-API-Key header"},
                    "403": {"description": "Invalid or revoked API key / IP-protected engine"},
                    "404": {"description": "Engine not registered"},
                }
            }
        }

    # Core proof pipeline paths
    paths["/api/v1/events"] = {
        "post": {
            "operationId": "ingestEvent",
            "summary": "Ingest a structured event for proof generation",
            "tags": ["proof-pipeline"],
            "security": [{"apiKey": []}],
            "requestBody": {
                "required": True,
                "content": {
                    "application/json": {
                        "schema": {
                            "type": "object",
                            "required": ["payload"],
                            "properties": {
                                "event_type": {"type": "string", "default": "generic_event"},
                                "payload": {"type": "object"},
                            }
                        }
                    }
                }
            },
            "responses": {"200": {"description": "Event ingested — returns event_id and transaction_id"}}
        }
    }

    paths["/api/v1/proof"] = {
        "post": {
            "operationId": "generateProof",
            "summary": "Generate Merkle proof for an ingested event",
            "tags": ["proof-pipeline"],
            "security": [{"apiKey": []}],
            "responses": {"200": {"description": "Merkle proof blob with compression ratio"}}
        }
    }

    paths["/api/v1/verify"] = {
        "post": {
            "operationId": "verifyProof",
            "summary": "Verify a proof against original or provided payload",
            "tags": ["proof-pipeline"],
            "security": [],
            "responses": {"200": {"description": "valid: true/false with recalculated root"}}
        }
    }

    paths["/api/v1/tokenize"] = {
        "post": {
            "operationId": "tokenizeEvent",
            "summary": "Mint a CLOUUD token from a proven event",
            "tags": ["proof-pipeline"],
            "security": [{"apiKey": []}],
            "responses": {"200": {"description": "Token minted — CLOUUD-DATA-{sha256[:8]} ID"}}
        }
    }

    paths["/api/v1/compress"] = {
        "post": {
            "operationId": "compressArtifact",
            "summary": "Compress a binary artifact (zstd/gzip) with Merkle provenance",
            "tags": ["compression"],
            "security": [{"apiKey": []}],
            "responses": {"200": {"description": "Artifact compressed — returns artifact_id, proof, download_url"}}
        }
    }

    paths["/api/v1/health"] = {
        "get": {
            "operationId": "healthCheck",
            "summary": "Service heartbeat",
            "tags": ["system"],
            "security": [],
            "responses": {"200": {"description": "ok + timestamp"}}
        }
    }

    return {
        "openapi": "3.1.0",
        "info": {
            "title": "UUON ecoPsystem API",
            "version": "1.0.0",
            "description": (
                "CLOUUD proof-of-state pipeline + UUON engine registry. "
                "F=(P,E,M,R,C) — Parameters, Expansion, Mapping, Rendering, Comprehension. "
                "USAL-1.0 licensed. Author: Phillip Aguilar Ruiz III / UUON Foundation Inc."
            ),
            "contact": {"email": "phi1@uuonfoundation.com"},
            "license": {"name": "USAL-1.0", "url": "https://github.com/UUON-Foundation"},
            "x-uuon": {
                "framework": "F=(P,E,M,R,C)",
                "author": "Phillip Aguilar Ruiz III",
                "org": "UUON Foundation Inc.",
                "github": "https://github.com/UUON-Foundation",
                "npm_scope": "@uuon-foundation",
            }
        },
        "servers": [{"url": BASE_URL, "description": "Production"}],
        "components": {
            "securitySchemes": {
                "apiKey": {
                    "type": "apiKey",
                    "in": "header",
                    "name": "X-API-Key",
                    "description": "Issue via GET /api/v1/api-keys (requires X-Admin-Key)"
                }
            }
        },
        "paths": paths,
    }


def _connector_manifest() -> dict:
    """
    Lightweight manifest for n8n / Make.com / MCP server registration.
    Declares engines as named connectors with explicit Input → Process → Output terminals.
    """
    connectors = []
    for eid, eng in ENGINES.items():
        connector = {
            "id": f"uuon-{eid}",
            "name": eng["name"],
            "description": eng["description"],
            "layer": eng["layer"],
            "bio": eng["bio"],
            "auth": {"type": "apiKey", "header": "X-API-Key"},
            "terminals": {
                "input": {
                    "type": "p_vector",
                    "endpoint": f"POST /api/v1/engines/{eid}",
                    "schema": eng["terminal_in"]["schema"],
                },
                "output": {
                    "type": eng["terminal_out"]["type"],
                    "formats": eng["terminal_out"]["formats"],
                    "description": eng["terminal_out"]["description"],
                },
                "stream": {
                    "available": eng["stream"],
                    "protocol": "WebSocket" if eng["stream"] else None,
                    "endpoint": eng.get("ws_endpoint"),
                    "message_in": "{ type: 'set_params', p_vector: {...} }",
                    "message_out": "{ type: 'frame', tick: N, output: {...}, provenance: {...} }",
                } if eng["stream"] else {"available": False},
            },
            "provenance": {
                "framework": "F=(P,E,M,R,C)",
                "license": "USAL-1.0",
                "author": "Phillip Aguilar Ruiz III / UUON Foundation Inc.",
                "proof": "CLOUUD_DETERMINISTIC_MERKLE — Merkle root of P-vector state",
            }
        }
        connectors.append(connector)

    return {
        "manifest_version": "1.0.0",
        "name": "UUON ecoPsystem Plugin",
        "description": "CLOUUD proof-of-state pipeline + UUON engine connectors. Input → Process → Output with USAL-1.0 provenance on every artifact.",
        "base_url": BASE_URL,
        "auth": {"type": "apiKey", "header": "X-API-Key", "issue_endpoint": "GET /api/v1/api-keys"},
        "websocket_base": BASE_URL.replace("https://", "wss://"),
        "connectors": connectors,
        "proof_pipeline": {
            "ingest": "POST /api/v1/events",
            "proof": "POST /api/v1/proof",
            "verify": "POST /api/v1/verify",
            "tokenize": "POST /api/v1/tokenize",
            "compress": "POST /api/v1/compress",
        },
        "license": "USAL-1.0",
        "author": "Phillip Aguilar Ruiz III / UUON Foundation Inc.",
        "github": "https://github.com/UUON-Foundation/ecoPsystem-api-socket",
    }


@router.get("/plugin/openapi.json", include_in_schema=False)
async def get_openapi():
    return _openapi_spec()


@router.get("/plugin/manifest")
async def get_manifest():
    return _connector_manifest()
