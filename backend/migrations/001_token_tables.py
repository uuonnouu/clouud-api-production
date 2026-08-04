import asyncio
import asyncpg
import os

DATABASE_URL = os.environ.get("DATABASE_URL")

async def migrate():
    conn = await asyncpg.connect(DATABASE_URL)
    
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS compression_tokens (
            token_id TEXT PRIMARY KEY,
            event_id TEXT REFERENCES events(event_id),
            artifact_id TEXT NOT NULL,
            filename TEXT,
            original_size BIGINT,
            compressed_size BIGINT,
            compression_ratio REAL,
            algorithm TEXT,
            sha256 TEXT,
            merkle_root TEXT,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
    """)
    print("compression_tokens: done")

    await conn.execute("""
        CREATE TABLE IF NOT EXISTS merkle_tokens (
            token_id TEXT PRIMARY KEY,
            event_id TEXT REFERENCES events(event_id),
            merkle_root TEXT NOT NULL,
            state_count INTEGER,
            chain_hashes JSONB,
            algorithm TEXT DEFAULT 'CLOUUD_DETERMINISTIC_MERKLE',
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
    """)
    print("merkle_tokens: done")

    await conn.execute("""
        CREATE TABLE IF NOT EXISTS shape_tokens (
            token_id TEXT PRIMARY KEY,
            event_id TEXT REFERENCES events(event_id),
            shape_name TEXT,
            parameters JSONB,
            formula TEXT,
            geometry_type TEXT,
            vertex_count INTEGER,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
    """)
    print("shape_tokens: done")

    await conn.execute("""
        CREATE TABLE IF NOT EXISTS fractal_tokens (
            token_id TEXT PRIMARY KEY,
            event_id TEXT REFERENCES events(event_id),
            fractal_type TEXT,
            iteration_depth INTEGER,
            parameters JSONB,
            merkle_root TEXT,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
    """)
    print("fractal_tokens: done")

    await conn.execute("""
        CREATE TABLE IF NOT EXISTS entropy_tokens (
            token_id TEXT PRIMARY KEY,
            event_id TEXT REFERENCES events(event_id),
            input_entropy REAL,
            output_entropy REAL,
            entropy_delta REAL,
            source_filename TEXT,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
    """)
    print("entropy_tokens: done")

    await conn.execute("""
        CREATE TABLE IF NOT EXISTS rally_tokens (
            token_id TEXT PRIMARY KEY,
            session_date TEXT NOT NULL,
            phase_line TEXT,
            merkle_root TEXT,
            summary JSONB,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
    """)
    print("rally_tokens: done")

    await conn.execute("""
        CREATE TABLE IF NOT EXISTS position_tokens (
            token_id TEXT PRIMARY KEY,
            event_id TEXT REFERENCES events(event_id),
            g_position INTEGER DEFAULT 33,
            reference_value REAL DEFAULT 100.0,
            coordinate JSONB,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
    """)
    print("position_tokens: done")

    await conn.close()
    print("migration complete")

asyncio.run(migrate())
