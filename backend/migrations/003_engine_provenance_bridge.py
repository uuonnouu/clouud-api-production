import asyncio
import asyncpg
import os

DATABASE_URL = os.environ["DATABASE_URL"]

ENGINES = [
    (
        "wave-field-3d",
        "Wave Field 3D Engine",
        3,
        "Skeletal System",
        True,
        "/api/v1/engines/wave-field-3d",
        "/ws/engines/wave-field-3d",
        "PUBLIC",
        None,
        None,
    ),
    (
        "phyllotaxis-seed",
        "Phyllotaxis Seed Engine",
        10,
        "Reproductive System — Seed Propagation",
        True,
        "/api/v1/engines/phyllotaxis-seed",
        "/ws/engines/phyllotaxis-seed",
        "PUBLIC",
        "https://uuon-foundation.github.io/phyllotaxis-seed-engine/",
        "@uuon-foundation/phyllotaxis-seed-engine@2.0.0",
    ),
    (
        "boundary-state",
        "Boundary State Engine",
        7,
        "Decision Layer — Prefrontal",
        True,
        "/api/v1/engines/boundary-state",
        "/ws/engines/boundary-state",
        "AUTH",
        None,
        None,
    ),
    (
        "propagation",
        "Propagation Engine",
        4,
        "Proprioception — Network State",
        True,
        "/api/v1/engines/propagation",
        "/ws/engines/propagation",
        "AUTH",
        None,
        None,
    ),
    (
        "pythagorean-graph",
        "Pythagorean Graph Engine",
        5,
        "Vascular Branching",
        False,
        "/api/v1/engines/pythagorean-graph",
        None,
        "PUBLIC",
        None,
        None,
    ),
]


async def migrate():
    conn = await asyncpg.connect(DATABASE_URL)

    await conn.execute("""
        CREATE TABLE IF NOT EXISTS engine_registry (
            engine_id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            layer INTEGER NOT NULL,
            bio TEXT,
            stream BOOLEAN NOT NULL DEFAULT FALSE,
            endpoint TEXT NOT NULL,
            ws_endpoint TEXT,
            auth TEXT,
            upstream TEXT,
            npm TEXT,
            call_count INTEGER NOT NULL DEFAULT 0,
            last_called TIMESTAMPTZ
        )
    """)

    await conn.execute("""
        CREATE TABLE IF NOT EXISTS engine_runs (
            run_id TEXT PRIMARY KEY,
            engine_id TEXT NOT NULL REFERENCES engine_registry(engine_id),
            layer INTEGER NOT NULL,
            bio TEXT,
            p_vector JSONB NOT NULL,
            output JSONB NOT NULL,
            provenance JSONB NOT NULL,
            merkle_root TEXT NOT NULL,
            p_vector_sha256 TEXT NOT NULL,
            output_format TEXT NOT NULL,
            processing_ms INTEGER NOT NULL,
            status TEXT NOT NULL,
            usal_1_0 TEXT NOT NULL,
            author TEXT NOT NULL,
            created_at TIMESTAMPTZ NOT NULL
        )
    """)

    await conn.execute("""
        CREATE TABLE IF NOT EXISTS provenance_chain (
            artifact_id TEXT PRIMARY KEY,
            artifact_type TEXT NOT NULL,
            engine_id TEXT NOT NULL,
            layer INTEGER NOT NULL,
            bio TEXT,
            framework TEXT NOT NULL,
            p_vector JSONB NOT NULL,
            p_vector_sha256 TEXT NOT NULL,
            merkle_root TEXT NOT NULL,
            usal_1_0 TEXT NOT NULL,
            author TEXT NOT NULL,
            utc_timestamp TIMESTAMPTZ NOT NULL,
            upstream_url TEXT,
            npm_package TEXT,
            proof JSONB NOT NULL
        )
    """)

    await conn.executemany("""
        INSERT INTO engine_registry (
            engine_id, name, layer, bio, stream,
            endpoint, ws_endpoint, auth, upstream, npm
        )
        VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10)
        ON CONFLICT (engine_id) DO UPDATE SET
            name = EXCLUDED.name,
            layer = EXCLUDED.layer,
            bio = EXCLUDED.bio,
            stream = EXCLUDED.stream,
            endpoint = EXCLUDED.endpoint,
            ws_endpoint = EXCLUDED.ws_endpoint,
            auth = EXCLUDED.auth,
            upstream = EXCLUDED.upstream,
            npm = EXCLUDED.npm
    """, ENGINES)

    await conn.close()
    print("003_engine_provenance_bridge: PASS")


if __name__ == "__main__":
    asyncio.run(migrate())
