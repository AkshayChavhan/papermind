# Deployment

> Status: **infrastructure written and verified locally. Deploying to a
> real VPS is pending** — this environment has no SSH/VPS access. See
> [`learning/13_deployment/01_vps_pm2_deployment.md`](../learning/13_deployment/01_vps_pm2_deployment.md)
> for what was actually run and proven before writing this.

## What's in this repo for deployment

- [`docker-compose.yml`](../docker-compose.yml) — runs Qdrant in **server
  mode** (a long-lived container other processes connect to over HTTP),
  instead of the local-mode file storage every notebook/demo has used so
  far. Server mode is required because two separate processes (the query
  service and the ingestion service) need to share one collection at the
  same time — local-mode's file lock only allows one process.
- [`ecosystem.config.js`](../ecosystem.config.js) — a PM2 config running
  all three services:
  - `papermind-api` — FastAPI query service (`backend/main_api.py`),
    port 8000
  - `papermind-ingestion` — Flask ingestion service
    (`backend/main_ingestion.py`), port 5001
  - `papermind-frontend` — the Next.js app (`npm start`), port 3000
- `backend/main_api.py` / `backend/main_ingestion.py` — production
  entrypoints that connect to Qdrant via `QDRANT_URL` (server mode),
  unlike `backend/run_api.py` / `backend/streamlit_app.py` which use
  local-mode and are for local development/demo only.

## Steps to deploy on a real VPS (pending real access — written, not yet run here)

1. Provision a VPS, install Docker, Node.js (for `npm`/PM2), and Python
   3.11+.
2. Clone the repo; create `backend/.venv` and
   `pip install -r backend/requirements.txt`; copy `backend/.env.example`
   to `backend/.env` and fill in the real `OPENAI_API_KEY` (and any other
   provider keys).
3. `cd frontend && npm install && npm run build` (production build).
4. `docker compose up -d` — starts Qdrant server mode on port 6333.
5. `npm install -g pm2` (or `npx pm2`), then from the repo root:
   `pm2 start ecosystem.config.js`.
6. `pm2 save && pm2 startup` so the services survive a reboot.
7. Put a reverse proxy (Nginx or similar) in front of ports 3000/8000 for
   a real domain + TLS — not configured here, since there's no domain or
   VPS yet to configure it for.

## What's verified vs. pending

| Piece | Status |
|---|---|
| `RetrievalPipeline` server-mode connection | **Verified** — real `docker compose up`, real `QdrantClient(url=...)` |
| Query service + ingestion service running as 2 separate live processes against the same collection | **Verified** — ingested via one process, queried via a different, simultaneously-running process, got a correctly-cited real answer |
| PM2 managing all 3 services (start/health/restart) | **Verified** — real local PM2 instance, all 3 came up healthy, restart tested on one without affecting the others |
| Real VPS provisioning, DNS, TLS, reverse proxy | **Pending** — no VPS/SSH access in this environment |
