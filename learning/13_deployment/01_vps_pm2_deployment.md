# 01 — Phase 11: Deployment to VPS with PM2 (server-mode Qdrant; live VPS pending)

## What's about to happen

Every piece has been built and verified locally. This task closes out the
one real deferred item that's been flagged since task #15: local-mode
Qdrant's single-process file lock, which meant the FastAPI query service
and Flask ingestion service could never run as two live, separate
processes at the same time. That's exactly what a real deployment needs —
both services up simultaneously, sharing one collection.

1. **Switch `RetrievalPipeline` to support Qdrant server mode** (connect
   over HTTP to a running `qdrant/qdrant` container) instead of only the
   local-mode file path used everywhere so far.
2. **Prove the fix for real**: run the Qdrant server (Docker), then run
   the FastAPI query service and the Flask ingestion service as two
   genuinely separate, simultaneously-running OS processes against it —
   something tasks #15/#17/#18 all explicitly deferred to this task.
3. **PM2 process management**: an `ecosystem.config.js` defining all three
   services (API, ingestion, Next.js frontend) as PM2-managed processes,
   tested with a real local PM2 instance.
4. **VPS deployment itself is pending** — there's no real VPS/SSH access
   available in this environment. What's buildable without one (the
   server-mode fix, the PM2 config, deployment docs) is built and
   verified; the actual "SSH onto a real box and run this" step is marked
   pending, the same way task #17 handled the missing LangSmith key.

## Why this way

**Server mode isn't a new idea introduced here — it's the one three
learning docs already said was coming**
`learning/08_api_services`, `learning/10_observability`, and
`learning/11_streamlit_demo` each independently flagged "local-mode
Qdrant can't run as two live processes; switching to server mode is
Phase 11's job." This task makes good on that instead of re-deciding
the approach from scratch.

**`RetrievalPipeline` gets an optional `url`, not a rewrite**
The existing `storage_path`-based constructor stays the default (every
notebook, the Streamlit app, and `run_api.py` keep working unchanged);
an optional `url` parameter switches `QdrantClient(path=...)` to
`QdrantClient(url=...)`. `qdrant-client` already supports both modes
through the same class — this is a config switch, not new retrieval
logic, so `retrieve()`/`ingest()` don't need to change at all.

**Verify the concurrency fix locally before writing it into deployment
docs**
Claiming "server mode fixes the lock problem" without actually starting
both processes at once and hitting both of them would be exactly the
kind of unverified claim this project has avoided everywhere else
(tasks #9, #13, #14, #16 all found real, sometimes surprising behavior by
actually running things). Docker was available locally, so the fix is
proven with a real `docker compose up`, two real separately-running
processes, and two real HTTP requests — not asserted on faith.

**PM2 config is written and tested locally with real PM2, but the actual
VPS step is explicitly marked pending**
A real deployment needs a real server with a public IP, SSH access, and
DNS/TLS decisions — none of which exist here. Writing an `ecosystem.
config.js` and confirming PM2 actually starts/stops/restarts the real
services with it (on this machine) is honest, verifiable progress.
Claiming the app is "deployed" without a real VPS would not be.

## Diagram

```
  docker compose up -d qdrant        (qdrant/qdrant, port 6333, volume-backed)
         │
         ├────────────────┬──────────────────────┐
         ▼                ▼                      ▼
  pm2: papermind-api  pm2: papermind-ingestion  pm2: papermind-frontend
  (uvicorn, FastAPI)  (Flask, /ingest)          (next start)
  QDRANT_URL=...      QDRANT_URL=...            NEXT_PUBLIC_API_URL=...
         │                │
         └────────────────┴──> same Qdrant server, same collection,
                                 both live at once (the fix)

  Real VPS deployment: pending (no SSH/VPS access in this environment).
  Everything above is written and verified locally; the remaining step
  is running the same `docker compose` + `pm2 start ecosystem.config.js`
  on a real server.
```

## What we did

1. Added `url: str | None` to `RetrievalPipeline.__init__` (alongside the
   existing `storage_path`) — `QdrantClient(url=...)` for server mode,
   unchanged `QdrantClient(path=...)` for local mode. Every existing
   caller (notebooks, Streamlit, `run_api.py`) keeps working unmodified.
2. Added `docker-compose.yml` (Qdrant server mode, port 6333, named
   volume) and two production entrypoints, `backend/main_api.py` /
   `backend/main_ingestion.py`, that read `QDRANT_URL` and don't
   auto-ingest a sample PDF (unlike the local demo entrypoints).
3. **Proved the concurrency fix for real, not just in docstrings.** Docker
   was available but its daemon wasn't running — started Docker Desktop,
   waited for the daemon, then:
   - `docker compose up -d` — a real Qdrant server container came up on
     port 6333.
   - Started the Flask ingestion service (`main_ingestion.py`) as one
     real process (port 5001) — confirmed healthy.
   - **While that process was still running**, started the FastAPI query
     service (`main_api.py`) as a second, separate real process (port
     8000) — confirmed healthy, with the ingestion process still
     answering `/health` at the same time.
   - Uploaded the real sample PDF through the live ingestion process:
     `{"chunks": 4}`.
   - Queried the live, *separate* query process:
     `{"answer": "...overlapping chunks of roughly five hundred tokens
     (page 3)...", "grounded": true, "pages": ["3", "2"]}` — a real,
     correctly-cited answer, served by a process that never ran the
     ingestion code, using data that arrived through a different process
     entirely. **This is the concrete proof** that server mode removes
     the local-mode limitation flagged in tasks #15/#17/#18.
4. Added `ecosystem.config.js` (3 PM2 apps: api, ingestion, frontend) and
   verified it with a real local PM2 instance (`npx pm2 start
   ecosystem.config.js`): all 3 came up and reported `online`, all 3
   health-checked successfully (including the Next.js production build
   from task #19 serving on port 3000), a real `/ask` request through the
   PM2-managed API process answered correctly, and `pm2 restart
   papermind-api` correctly restarted only that one process (new PID, `↺`
   counter incremented) while the other two kept running undisturbed.
5. Added `docs/DEPLOYMENT.md` summarizing what's verified vs. pending.
6. Cleaned up afterward: `pm2 delete all`, `pm2 kill`, `docker compose
   down` — nothing was left running.
7. **Pending**: an actual VPS. Everything above runs on this local
   machine with a local Docker daemon and a local PM2 instance — real
   SSH access to a real server, DNS, and TLS/reverse-proxy configuration
   are the remaining, genuinely external-dependent steps, tracked in
   `docs/DEPLOYMENT.md` and noted in memory for this project (see the
   pending-items list) rather than silently skipped or faked.
