# CLOUUD Frontend Dashboard

This frontend is the React dashboard for the CLOUUD engine unit in `clouud-api-production`.

It is the user-facing layer of the repo: it connects to the backend API, displays engine status, and helps visualize proof generation and verification outcomes.

## What This App Does

- renders the CLOUUD engine dashboard,
- communicates with the FastAPI backend,
- visualizes data ingestion and proof artifact status,
- gives developers a place to explore the engine as a unit.

## Project Structure

- `public/` — static HTML and assets.
- `src/` — React app source code and UI components.
- `package.json` — app dependencies and scripts.

## Available Scripts

In the project directory, run:

### `npm start`

Runs the app in development mode. Open [http://localhost:3000](http://localhost:3000) to view it.

### `npm test`

Launches the test runner in interactive watch mode.

### `npm run build`

Builds the app for production into the `build` folder.

## Notes

This frontend is part of the larger CLOUUD engine repo and is meant to be used alongside the backend service in `backend/`.

If you are deploying the app, ensure the backend API is available and the frontend is configured to point at the correct service endpoint.

## Backend Integration

The backend service is documented in `backend/README.md`. Run the backend separately and configure the frontend to use the backend base URL.

Example environment variables:

```bash
REACT_APP_API_BASE_URL=http://localhost:8000/api/v1
```

## Documentation Gap

This file is currently a generic frontend readme and should be enhanced with:

- actual CLOUUD dashboard usage,
- API endpoint contracts,
- environment variable setup,
- deployment instructions,
- IoT/edge dashboard scenarios,
- and how to run local engine integration tests.
