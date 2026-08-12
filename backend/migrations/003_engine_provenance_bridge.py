import asyncio
import asyncpg
import os

DATABASE_URL = os.environ["DATABASE_URL"]


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

    await conn.close()
    print("003_engine_provenance_bridge: PASS")


if __name__ == "__main__":
    asyncio.run(migrate())
