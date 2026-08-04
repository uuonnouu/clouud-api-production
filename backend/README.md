# Backend: CLOUUD API Service

This backend implements the CLOUUD proof pipeline and event storage using PostgreSQL. It is designed to work with Neon database storage but can also run against any PostgreSQL-compatible endpoint.

## Environment

The backend requires the following environment variables:

- `DATABASE_URL` — Postgres connection string (`postgresql://user:pass@host:port/dbname`)
- `ADMIN_KEY` — strong admin key for protected operations

### Example `.env`

```
DATABASE_URL=postgresql://username:password@host:5432/clouud
ADMIN_KEY=your-admin-secret
```

## Run locally

1. Install dependencies:

```bash
cd backend
pip install -r requirements.txt
```

2. Start the server:

```bash
uvicorn server:app --reload --host 0.0.0.0 --port 8000
```

3. Use the API endpoints:

- `GET /api/v1/health`
- `GET /api/v1/api-keys` (admin key required)
- `POST /api/v1/events`
- `POST /api/v1/proof`
- `POST /api/v1/verify`
- `POST /api/v1/tokenize`
- `POST /api/v1/tamper` (admin key required)
- `POST /api/v1/admin/trigger-retention` (admin key required)

## Testing

Run the backend unit tests with:

```bash
cd backend
pytest -q tests/test_server.py
```

## Neon support

If you already have Neon database access, set `DATABASE_URL` to your Neon connection string. You do not need Railway for storage if Neon is available. Railway is only useful if you want a hosted backend service as well.

## Notes

- The backend now persists events, API keys, proof artifacts, and tokens in PostgreSQL.
- Admin endpoints require the value of `X-Admin-Key` to match `ADMIN_KEY`.
- Regular event ingestion requires `X-API-Key`.
- The backend now uses FastAPI lifespan handling for startup and shutdown.
- The backend remains a prototype proof flow; the goal is to make it production-ready with compact artifacts and stronger verification.
