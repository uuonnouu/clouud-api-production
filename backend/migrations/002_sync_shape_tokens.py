"""
Sync shape_tokens table in clouud DB from dmension shape data.
Reads: NEON_DATABASE_URL (dmension)
Writes: DATABASE_URL (clouud)
"""
import asyncio
import asyncpg
import os
import uuid
from datetime import datetime, timezone

DMENSION_URL = os.environ.get("NEON_DATABASE_URL")
CLOUUD_URL = os.environ.get("DATABASE_URL")

async def sync():
    print("Connecting to dmension...")
    src = await asyncpg.connect(DMENSION_URL)
    
    print("Connecting to clouud...")
    dst = await asyncpg.connect(CLOUUD_URL)

    # Pull shapes from dmension
    shapes = await src.fetch("""
        SELECT shape_type, parameters, formula, geometry_type, vertex_count
        FROM formula_implementations
        LIMIT 100
    """)
    print(f"Found {len(shapes)} shapes in dmension")

    inserted = 0
    for s in shapes:
        token_id = f"SHAPE-{str(uuid.uuid4())[:8].upper()}"
        try:
            await dst.execute("""
                INSERT INTO shape_tokens (token_id, shape_name, parameters, formula, geometry_type, vertex_count)
                VALUES ($1, $2, $3, $4, $5, $6)
                ON CONFLICT (token_id) DO NOTHING
            """,
                token_id,
                s.get("shape_type"),
                str(s.get("parameters") or "{}"),
                s.get("formula"),
                s.get("geometry_type"),
                s.get("vertex_count"),
            )
            inserted += 1
        except Exception as e:
            print(f"  skip {s.get('shape_type')}: {e}")

    print(f"Synced {inserted} shape tokens to clouud")
    await src.close()
    await dst.close()

asyncio.run(sync())
