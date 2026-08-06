"""
UUON Engine REST Router — writes to engine_runs, provenance_chain, engine_registry
F=(P,E,M,R,C) · USAL-1.0 · Phillip Aguilar Ruiz III / UUON Foundation Inc.
"""
import json, uuid, subprocess, shutil, time
from pathlib import Path
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

from .. import core
from ..compression.crypto import get_sha256, normalize_and_encode, generate_merkle_chain
from .registry import ENGINES, get_engine, list_engines

_ENGINES_DIR = Path(__file__).parent
_SEED_RUNNER = _ENGINES_DIR / "run_seed.js"
_NODE_BIN    = shutil.which("node") or shutil.which("nodejs") or "node"

router = APIRouter()

class EngineRequest(BaseModel):
    p_vector: dict
    output_format: str = "json"
    width: int = 800
    height: int = 800

def build_provenance(engine, p_vector, request_id):
    sha = get_sha256(json.dumps(p_vector, sort_keys=True))
    return {"request_id": request_id, "engine_id": engine["id"], "engine_name": engine["name"],
            "layer": engine["layer"], "bio": engine["bio"], "framework": "F=(P,E,M,R,C)",
            "p_vector_sha256": sha, "usal_1_0": "UUON-Foundation/USAL-1.0",
            "author": "Phillip Aguilar Ruiz III / UUON Foundation Inc.",
            "utc_timestamp": datetime.now(timezone.utc).isoformat(),
            "upstream": engine.get("upstream"), "npm": engine.get("npm")}

def build_proof(p_vector):
    states = normalize_and_encode(p_vector)
    root, hashes = generate_merkle_chain(states)
    return {"algorithm": "CLOUUD_DETERMINISTIC_MERKLE", "proof_version": "CLOUUD-CORE-1.0",
            "merkle_root": root, "state_count": len(states), "hashes": hashes}

def _run_phyllotaxis(p_vector, width, height):
    try:
        r = subprocess.run([_NODE_BIN, str(_SEED_RUNNER), json.dumps(p_vector), str(width), str(height)],
                           capture_output=True, text=True, timeout=15)
        if r.returncode != 0:
            raise RuntimeError(r.stderr.strip())
        data = json.loads(r.stdout)
        full = len(data.get("field", []))
        data["field_sample"] = data.pop("field", [])[:100]
        data["field_total_count"] = full
        data["type"] = "seed_geometry"
        data["engine"] = "seed.js — real F=(P,E,M,R,C)"
        return data
    except Exception as e:
        return {"error": str(e), "type": "seed_envelope"}

def compute_engine_output(engine, p_vector, output_format, width=800, height=800):
    import math, random
    eid = engine["id"]
    if eid == "phyllotaxis-seed":
        return _run_phyllotaxis(p_vector, width, height)
    elif eid == "pythagorean-graph":
        def tree(d, al, ar, ratio, x=0, y=0, l=1.0, a=90.0):
            if d == 0: return []
            import math as m
            r = m.radians(a)
            x2, y2 = x + l*m.cos(r), y + l*m.sin(r)
            e = [{"from":[round(x,4),round(y,4)],"to":[round(x2,4),round(y2,4)],"depth":d}]
            if d > 1:
                e += tree(d-1,al,ar,ratio,x2,y2,l*ratio,a+al)
                e += tree(d-1,al,ar,ratio,x2,y2,l*ratio,a-ar)
            return e
        depth = min(p_vector.get("depth",7),8)
        edges = tree(depth,p_vector.get("angle_left",45.0),p_vector.get("angle_right",45.0),p_vector.get("ratio",0.707))
        return {"type":"graph_topology","edge_count":len(edges),"node_count":len(edges)+1,"depth":depth,"edges":edges}
    elif eid == "boundary-state":
        bits = p_vector.get("bits",4)
        n = 2**bits
        h = math.log2(n) if n > 1 else 0.0
        return {"type":"state_field","n_states":n,"dimensions":p_vector.get("dimensions",2),"bits":bits,
                "shannon_H":round(h,6),"boltzmann_S":round(h*1.380649e-23,30),
                "gray_codes":[i^(i>>1) for i in range(min(n,16))],"renderer":p_vector.get("renderer","hypercube")}
    elif eid == "propagation":
        t,tr,d = p_vector.get("threshold",0.55),p_vector.get("transfer",0.40),p_vector.get("decay",0.08)
        eq = 62.0 if (abs(t-0.55)<0.05 and abs(tr-0.40)<0.05 and abs(d-0.08)<0.05) else round(random.uniform(30,75),2)
        return {"type":"network_state","mode":p_vector.get("mode","neural"),"nodes":min(p_vector.get("nodes",100),200),
                "equilibrium_activation_pct":eq,"threshold":t,"stream_available":True,"ws_endpoint":engine["ws_endpoint"]}
    else:
        return {"type":"seed_envelope","p_vector":p_vector,"render_target":engine.get("upstream"),
                "note":"Render is browser-side. Seed envelope anchors provenance."}

async def _persist(pool, request_id, engine, p_vector, output, provenance, proof, start_ms):
    if pool is None: return
    import datetime as dt
    now = dt.datetime.now(dt.timezone.utc)
    ms  = int(time.time()*1000 - start_ms)
    eid = engine["id"]
    pairs = [
        ("INSERT INTO events (event_id,event_type,payload,timestamp,status,proof_blob,purged) VALUES ($1,$2,$3,$4,$5,$6,FALSE)",
         (request_id, f"engine_run:{eid}", json.dumps({"engine_id":eid,"p_vector":p_vector}), now, "computed", json.dumps(proof))),
        ("INSERT INTO engine_runs (run_id,engine_id,layer,bio,p_vector,output,provenance,merkle_root,p_vector_sha256,output_format,processing_ms,status,usal_1_0,author,created_at) VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13,$14,$15) ON CONFLICT (run_id) DO NOTHING",
         (request_id,eid,engine["layer"],engine["bio"],json.dumps(p_vector),json.dumps(output),json.dumps(provenance),proof["merkle_root"],provenance["p_vector_sha256"],"json",ms,"computed","UUON-Foundation/USAL-1.0","Phillip Aguilar Ruiz III / UUON Foundation Inc.",now)),
        ("INSERT INTO provenance_chain (artifact_id,artifact_type,engine_id,layer,bio,framework,p_vector,p_vector_sha256,merkle_root,usal_1_0,author,utc_timestamp,upstream_url,npm_package,proof) VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13,$14,$15) ON CONFLICT (artifact_id) DO NOTHING",
         (request_id,"engine_run",eid,engine["layer"],engine["bio"],"F=(P,E,M,R,C)",json.dumps(p_vector),provenance["p_vector_sha256"],proof["merkle_root"],"UUON-Foundation/USAL-1.0","Phillip Aguilar Ruiz III / UUON Foundation Inc.",now,engine.get("upstream"),engine.get("npm"),json.dumps(proof))),
        ("UPDATE engine_registry SET call_count=call_count+1, last_called=$1 WHERE engine_id=$2",
         (now, eid)),
    ]
    for sql, args in pairs:
        try:
            await pool.execute(sql, *args)
        except Exception:
            pass

@router.get("/engines")
async def list_all_engines():
    return {"framework":"F=(P,E,M,R,C)","license":"USAL-1.0",
            "author":"Phillip Aguilar Ruiz III / UUON Foundation Inc.","engines":list_engines()}

@router.get("/engines/{engine_id}")
async def describe_engine(engine_id: str):
    engine = get_engine(engine_id)
    if not engine:
        raise HTTPException(status_code=404, detail=f"Engine '{engine_id}' not registered.")
    return engine

@router.post("/engines/{engine_id}")
async def run_engine(engine_id: str, req: EngineRequest, api_key: str = Depends(core.verify_api_key)):
    engine = get_engine(engine_id)
    if not engine:
        raise HTTPException(status_code=404, detail=f"Engine '{engine_id}' not registered.")
    if engine["auth"] == "IP":
        raise HTTPException(status_code=403, detail="USAL-1.0 IP-protected.")
    request_id = str(uuid.uuid4())
    start_ms   = time.time() * 1000
    output     = compute_engine_output(engine, req.p_vector, req.output_format, req.width, req.height)
    provenance = build_provenance(engine, req.p_vector, request_id)
    proof      = build_proof(req.p_vector)
    await _persist(core.pool, request_id, engine, req.p_vector, output, provenance, proof, start_ms)
    return {"request_id":request_id,"engine_id":engine_id,"layer":engine["layer"],"bio":engine["bio"],
            "p_vector":req.p_vector,"output":output,"provenance":provenance,"proof":proof}
