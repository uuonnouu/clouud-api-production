"""
UUON Engine Registry
F=(P,E,M,R,C) — Parameters, Expansion, Mapping, Rendering, Comprehension

Each engine entry defines:
  - id:           unique engine slug
  - layer:        clouud biological layer number
  - bio:          biological system mapped to
  - terminal_in:  what the engine accepts (P-vector schema)
  - terminal_out: what the engine produces
  - stream:       whether this engine supports WebSocket streaming
  - endpoint:     REST path on this server
  - upstream:     live upstream URL (uuon.world or Railway)
  - auth:         PUBLIC | AUTH | IP
"""

ENGINES = {
    "wave-field-3d": {
        "id": "wave-field-3d",
        "name": "Wave Field 3D Engine",
        "layer": 3,
        "bio": "Skeletal System",
        "description": "Parametric wave-deformation engine for 3D geometry. F=(P,E,M,R,C).",
        "terminal_in": {
            "type": "p_vector",
            "schema": {
                "shape": {"type": "string", "enum": ["sphere", "cube", "torus", "pyramid", "cylinder"], "default": "sphere"},
                "algorithm": {"type": "string", "description": "WFE algorithm key e.g. F1, G2, N3", "default": "F1"},
                "amplitude": {"type": "number", "min": 0.0, "max": 2.0, "default": 0.3},
                "frequency": {"type": "number", "min": 0.1, "max": 10.0, "default": 1.0},
                "speed": {"type": "number", "min": 0.0, "max": 5.0, "default": 1.0},
                "octaves": {"type": "integer", "min": 1, "max": 8, "default": 1},
            }
        },
        "terminal_out": {
            "type": "geometry_stream",
            "formats": ["glb", "obj", "frame_json"],
            "description": "Animated 3D geometry. GLB with morph targets or per-frame vertex positions."
        },
        "stream": True,
        "endpoint": "/api/v1/engines/wave-field-3d",
        "ws_endpoint": "/ws/engines/wave-field-3d",
        "upstream": "https://uuon-foundation.github.io/wave-field-3d-engine/",
        "npm": "@uuon-foundation/wave-field-3d-engine@1.0.1",
        "auth": "PUBLIC",
    },

    "phyllotaxis-seed": {
        "id": "phyllotaxis-seed",
        "name": "Phyllotaxis Seed Engine",
        "layer": 10,
        "bio": "Reproductive System — Seed Propagation",
        "description": "Irrational packing, parametric provenance, compression fidelity. Golden angle spiral geometry.",
        "terminal_in": {
            "type": "p_vector",
            "schema": {
                "seeds": {"type": "integer", "min": 1, "max": 10000, "default": 4000},
                "arms": {"type": "integer", "min": 1, "max": 89, "default": 13},
                "twist": {"type": "number", "min": 0.0, "max": 2.0, "default": 0.68},
                "warp": {"type": "number", "min": 0.0, "max": 10.0, "default": 2.50},
                "spread": {"type": "number", "min": 0.1, "max": 10.0, "default": 3.4},
                "radius": {"type": "number", "min": 0.1, "max": 20.0, "default": 4.2},
                "rings": {"type": "integer", "min": 1, "max": 89, "default": 17},
            }
        },
        "terminal_out": {
            "type": "seed_geometry",
            "formats": ["canvas2d_frame", "svg", "seed_json"],
            "description": "Phyllotactic point cloud with layer and texture encoding."
        },
        "stream": True,
        "endpoint": "/api/v1/engines/phyllotaxis-seed",
        "ws_endpoint": "/ws/engines/phyllotaxis-seed",
        "upstream": "https://uuon-foundation.github.io/phyllotaxis-seed-engine/",
        "npm": "@uuon-foundation/phyllotaxis-seed-engine@1.0.0",
        "auth": "PUBLIC",
    },

    "boundary-state": {
        "id": "boundary-state",
        "name": "Boundary State Engine",
        "layer": 7,
        "bio": "Decision Layer — Prefrontal",
        "description": "Binary boundary systems. 2^n states, 0D–3D hypercube geometry. Shannon entropy, Boltzmann S, Gray code.",
        "terminal_in": {
            "type": "p_vector",
            "schema": {
                "dimensions": {"type": "integer", "min": 0, "max": 3, "default": 2},
                "bits": {"type": "integer", "min": 1, "max": 16, "default": 4},
                "distribution": {"type": "string", "enum": ["uniform", "gaussian", "exponential", "custom"], "default": "uniform"},
                "renderer": {"type": "string", "enum": ["hypercube", "entropy_map", "gray_code", "boltzmann"], "default": "hypercube"},
            }
        },
        "terminal_out": {
            "type": "state_field",
            "formats": ["entropy_json", "state_map", "vertex_positions"],
            "description": "State space geometry with Shannon entropy H, Boltzmann S, efficiency ratio."
        },
        "stream": True,
        "endpoint": "/api/v1/engines/boundary-state",
        "ws_endpoint": "/ws/engines/boundary-state",
        "upstream": "https://uuon.world/api/engines/bse",
        "auth": "AUTH",
    },

    "propagation": {
        "id": "propagation",
        "name": "Propagation Engine",
        "layer": 4,
        "bio": "Proprioception — Network State",
        "description": "State change through connected graph networks. Neural/small-world, Stress/grid, Epidemic/random modes.",
        "terminal_in": {
            "type": "p_vector",
            "schema": {
                "mode": {"type": "string", "enum": ["neural", "stress", "epidemic"], "default": "neural"},
                "nodes": {"type": "integer", "min": 10, "max": 500, "default": 100},
                "threshold": {"type": "number", "min": 0.0, "max": 1.0, "default": 0.55},
                "transfer": {"type": "number", "min": 0.0, "max": 1.0, "default": 0.40},
                "decay": {"type": "number", "min": 0.0, "max": 1.0, "default": 0.08},
                "refractory": {"type": "integer", "min": 0, "max": 100, "default": 18},
                "rewire": {"type": "number", "min": 0.0, "max": 1.0, "default": 0.15},
            }
        },
        "terminal_out": {
            "type": "network_state_stream",
            "formats": ["tick_json", "activation_map", "edge_traffic"],
            "description": "Per-tick network activation state. Reentrant excitation equilibrium observable at ~62% activation."
        },
        "stream": True,
        "endpoint": "/api/v1/engines/propagation",
        "ws_endpoint": "/ws/engines/propagation",
        "upstream": "https://uuon.world/api/engines/propagation",
        "auth": "AUTH",
    },

    "pythagorean-graph": {
        "id": "pythagorean-graph",
        "name": "Pythagorean Graph Engine",
        "layer": 5,
        "bio": "Vascular Branching",
        "description": "Recursive Pythagorean tree topology. Graph export serializes full recursive topology to JSON with provenance metadata per node.",
        "terminal_in": {
            "type": "p_vector",
            "schema": {
                "depth": {"type": "integer", "min": 1, "max": 12, "default": 7},
                "angle_left": {"type": "number", "min": 0.0, "max": 90.0, "default": 45.0},
                "angle_right": {"type": "number", "min": 0.0, "max": 90.0, "default": 45.0},
                "ratio": {"type": "number", "min": 0.1, "max": 0.9, "default": 0.707},
            }
        },
        "terminal_out": {
            "type": "graph_topology",
            "formats": ["graph_json", "svg", "edge_list"],
            "description": "Recursive branching graph with provenance metadata per node (Murray's Law topology)."
        },
        "stream": False,
        "endpoint": "/api/v1/engines/pythagorean-graph",
        "ws_endpoint": None,
        "upstream": "https://uuon-foundation.github.io/pythagorean-graph-engine/",
        "npm": "@uuon-foundation/pythagorean-graph-engine@1.0.0",
        "auth": "PUBLIC",
    },
}


def get_engine(engine_id: str) -> dict | None:
    return ENGINES.get(engine_id)


def list_engines() -> list[dict]:
    return [
        {
            "id": e["id"],
            "name": e["name"],
            "layer": e["layer"],
            "bio": e["bio"],
            "stream": e["stream"],
            "endpoint": e["endpoint"],
            "ws_endpoint": e["ws_endpoint"],
            "auth": e["auth"],
        }
        for e in ENGINES.values()
    ]
