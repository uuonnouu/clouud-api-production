"""
UUON Engine WebSocket Layer
wss://host/ws/engines/{engine_id}

Protocol:
  CLIENT → SERVER:
    { "type": "set_params", "p_vector": {...} }      — update parameters, continue streaming
    { "type": "ping" }                                — keepalive
    { "type": "stop" }                                — stop stream, close

  SERVER → CLIENT:
    { "type": "connected", "engine_id": ..., "layer": ..., "bio": ... }
    { "type": "frame", "tick": N, "output": {...}, "provenance": {...} }
    { "type": "error", "detail": "..." }
    { "type": "pong" }

Streaming engines:  wave-field-3d, phyllotaxis-seed, boundary-state, propagation
Non-streaming:      pythagorean-graph (REST only — graph is static per P-vector)
"""

import asyncio
import json
import math
import time
import uuid
from datetime import datetime, timezone

from fastapi import WebSocket, WebSocketDisconnect
from starlette.websockets import WebSocketState

from .registry import get_engine
from .router import compute_engine_output, build_provenance, build_proof


# ── Tick generators per engine ─────────────────────────────────────────────────

def _tick_wave_field(p_vector: dict, tick: int) -> dict:
    """
    Server-side tick: returns amplitude envelope + phase for the current tick.
    Full vertex geometry runs client-side in Three.js.
    This stream carries the parameter state so a headless client can reconstruct.
    """
    t = tick * p_vector.get("speed", 1.0) * 0.016  # ~60fps equivalent
    freq = p_vector.get("frequency", 1.0)
    amp = p_vector.get("amplitude", 0.3)
    phase = (math.sin(2 * math.pi * freq * t) * amp)
    return {
        "tick": tick,
        "t": round(t, 6),
        "phase": round(phase, 6),
        "amplitude_envelope": round(abs(phase), 6),
        "p_vector": p_vector,
    }


def _tick_phyllotaxis(p_vector: dict, tick: int) -> dict:
    """
    Per-tick seed reveal — streams individual seed positions incrementally.
    Useful for animating growth from 0 → N seeds.
    """
    golden_angle = math.pi * (3.0 - math.sqrt(5.0))
    twist = p_vector.get("twist", 0.68)
    spread = p_vector.get("spread", 3.4)
    radius = p_vector.get("radius", 4.2)
    arms = p_vector.get("arms", 13)
    total = p_vector.get("seeds", 4000)
    effective_angle = golden_angle * twist

    i = tick % total
    r = spread * math.sqrt(i / total) * radius
    theta = i * effective_angle
    return {
        "tick": tick,
        "seed_index": i,
        "x": round(r * math.cos(theta), 6),
        "y": round(r * math.sin(theta), 6),
        "arm": i % arms,
        "total_seeds": total,
    }


def _tick_boundary_state(p_vector: dict, tick: int) -> dict:
    """
    Cycles through state transitions in Gray code order.
    Each tick = one state transition in the boundary system.
    """
    bits = p_vector.get("bits", 4)
    n_states = 2 ** bits
    state_index = tick % n_states
    gray = state_index ^ (state_index >> 1)
    binary = format(gray, f'0{bits}b')
    import hashlib
    h = hashlib.sha256(binary.encode()).hexdigest()[:16]
    return {
        "tick": tick,
        "state_index": state_index,
        "gray_code": gray,
        "binary": binary,
        "state_hash": h,
        "n_states": n_states,
    }


def _tick_propagation(p_vector: dict, tick: int) -> dict:
    """
    Simulates one propagation tick on a small synthetic network.
    Returns activation fraction — converges toward equilibrium.
    """
    import random
    threshold = p_vector.get("threshold", 0.55)
    transfer = p_vector.get("transfer", 0.40)
    decay = p_vector.get("decay", 0.08)
    # Sigmoid convergence toward documented ~62% equilibrium
    target = 0.62
    activation = target * (1 - math.exp(-tick * transfer * 0.1))
    activation += random.gauss(0, 0.01)  # biological noise
    activation = max(0.0, min(1.0, activation))
    return {
        "tick": tick,
        "activation_fraction": round(activation, 6),
        "activation_pct": round(activation * 100, 2),
        "threshold": threshold,
        "mode": p_vector.get("mode", "neural"),
        "equilibrium_target": target,
    }


_TICK_FN = {
    "wave-field-3d": _tick_wave_field,
    "phyllotaxis-seed": _tick_phyllotaxis,
    "boundary-state": _tick_boundary_state,
    "propagation": _tick_propagation,
}


# ── WebSocket handler ──────────────────────────────────────────────────────────

async def engine_websocket(websocket: WebSocket, engine_id: str):
    """
    Mount point: websocket_route("/ws/engines/{engine_id}")
    Handles the full lifecycle: connect → stream → update params → disconnect.
    """
    engine = get_engine(engine_id)

    await websocket.accept()

    if not engine:
        await websocket.send_json({"type": "error", "detail": f"Engine '{engine_id}' not registered."})
        await websocket.close()
        return

    if not engine.get("stream"):
        await websocket.send_json({"type": "error", "detail": f"Engine '{engine_id}' does not support streaming. Use REST endpoint."})
        await websocket.close()
        return

    tick_fn = _TICK_FN.get(engine_id)
    if not tick_fn:
        await websocket.send_json({"type": "error", "detail": f"No tick function registered for '{engine_id}'."})
        await websocket.close()
        return

    # Send connection confirmation
    await websocket.send_json({
        "type": "connected",
        "engine_id": engine_id,
        "name": engine["name"],
        "layer": engine["layer"],
        "bio": engine["bio"],
        "framework": "F=(P,E,M,R,C)",
        "license": "USAL-1.0",
        "utc": datetime.now(timezone.utc).isoformat(),
    })

    # Default P-vector from registry schema defaults
    p_vector = {
        k: v.get("default")
        for k, v in engine["terminal_in"]["schema"].items()
        if "default" in v
    }

    tick = 0
    # ~30 ticks/sec — adequate for parameter streaming without overloading
    TICK_INTERVAL = 1.0 / 30.0
    running = True

    async def stream_loop():
        nonlocal tick, p_vector, running
        while running:
            if websocket.client_state != WebSocketState.CONNECTED:
                break
            try:
                frame_data = tick_fn(p_vector, tick)
                provenance_seed = {
                    "engine_id": engine_id,
                    "tick": tick,
                    "p_vector_sha256": build_proof(p_vector)["merkle_root"],
                }
                await websocket.send_json({
                    "type": "frame",
                    "tick": tick,
                    "output": frame_data,
                    "provenance": {
                        "engine_id": engine_id,
                        "layer": engine["layer"],
                        "framework": "F=(P,E,M,R,C)",
                        "usal_1_0": "UUON-Foundation/USAL-1.0",
                        "merkle_seed": provenance_seed["p_vector_sha256"],
                        "utc": datetime.now(timezone.utc).isoformat(),
                    },
                })
                tick += 1
            except Exception as e:
                await websocket.send_json({"type": "error", "detail": str(e)})
                break
            await asyncio.sleep(TICK_INTERVAL)

    async def receive_loop():
        nonlocal p_vector, running
        while running:
            try:
                raw = await websocket.receive_text()
                msg = json.loads(raw)
                msg_type = msg.get("type")

                if msg_type == "set_params":
                    new_p = msg.get("p_vector", {})
                    p_vector = {**p_vector, **new_p}
                    await websocket.send_json({"type": "params_updated", "p_vector": p_vector})

                elif msg_type == "ping":
                    await websocket.send_json({"type": "pong", "tick": tick})

                elif msg_type == "stop":
                    running = False
                    break

            except WebSocketDisconnect:
                running = False
                break
            except json.JSONDecodeError:
                await websocket.send_json({"type": "error", "detail": "Invalid JSON in message."})
            except Exception:
                running = False
                break

    # Run both loops concurrently — stream + receive in parallel
    try:
        await asyncio.gather(stream_loop(), receive_loop())
    except Exception:
        pass
    finally:
        running = False
        if websocket.client_state == WebSocketState.CONNECTED:
            await websocket.close()
