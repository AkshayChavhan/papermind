# 01 — Phase 6: FastAPI query service + Flask ingestion service

## What's about to happen

So far every piece (ingestion, retrieval, the LangGraph workflow) has only
ever been called from inside a notebook process. Phase 6 exposes two of
them over HTTP, as two separate small services, matching the stack
decision in `ARCHITECTURE.md` ("API: FastAPI (main), Flask (ingestion
service)"):

1. **Flask ingestion service** (`backend/src/services/ingestion_service.py`)
   — `POST /ingest` accepts an uploaded PDF, runs
   `RetrievalPipeline.ingest()`, returns the chunk count.
2. **FastAPI query service** (`backend/src/services/api.py`) — `POST /ask`
   accepts `{"question": "..."}`, runs the Phase 5 LangGraph workflow,
   returns `{"answer", "chunks", "grounded"}`.

Both get a `GET /health` endpoint.

## Why this way

**Two separate services, because ingestion and querying are different
workloads**
Ingestion is occasional and write-heavy (parse, chunk, embed, upsert);
querying is frequent and read-heavy. Splitting them means each can be
scaled, deployed, or rate-limited independently later — this is the
reason the stack decision calls for two frameworks, not one, even though
either framework could technically do both jobs.

**A real constraint this surfaces: local-mode Qdrant is single-process**
Task #5 chose Qdrant's embedded "local mode" (a file on disk, no Docker)
specifically to avoid running a server. That file storage uses a file
lock — only one process can hold a `QdrantClient(path=...)` open on it at
a time. Two *separate OS processes* (`flask run` and `uvicorn`, each
opening their own `RetrievalPipeline`) would fight over that same lock the
moment both are live simultaneously. This is a real trade-off, not a bug
to patch around:
- For this task, both services are verified independently, in-process,
  with each framework's own test client (`flask.testing.FlaskClient`,
  `fastapi.testing.TestClient`) — never as two simultaneously-running
  live servers against the same local Qdrant path.
- The actual fix — pointing both services at a Qdrant **server** instance
  (Docker or hosted) instead of local-mode — is exactly the kind of change
  Phase 11 (deployment) should make, not something to quietly work around
  here by merging the services back into one, which would undo the reason
  for splitting them in the first place.

**Dependency injection for the pipeline/LLM, not module-level globals**
Both services take a `RetrievalPipeline` (and the FastAPI service also
takes the compiled graph) as constructor arguments to their app factories,
rather than constructing them at import time. This is what makes testing
both services in one notebook process possible without double-opening
Qdrant — the test code builds one `RetrievalPipeline`, hands it to
whichever app factory it's exercising, and the import-time cost (loading
embedding models) only happens once.

## Diagram

```
                PDF upload                      question
                    │                               │
                    ▼                               ▼
     ┌───────────────────────────┐    ┌───────────────────────────┐
     │ Flask ingestion service    │    │ FastAPI query service      │
     │ POST /ingest                │    │ POST /ask                   │
     │   -> RetrievalPipeline      │    │   -> LangGraph workflow     │
     │      .ingest(pdf)            │    │      (Phase 5)               │
     │   <- {"chunks": N}           │    │   <- {"answer", "chunks",   │
     └───────────────────────────┘    │       "grounded"}            │
                    │                  └───────────────────────────┘
                    └──────────► same Qdrant collection ◄──────────┘
                         (local-mode file; one process at a time —
                          see "Why this way" for the real constraint)
```

## What we did

1. Added `backend/src/services/ingestion_service.py`: Flask app factory
   `create_app(pipeline)` with `GET /health` and `POST /ingest` (multipart
   file upload, sanitized via `werkzeug.utils.secure_filename`, saved to
   `data/uploads/`, then `pipeline.ingest(path)`).
2. Added `backend/src/services/api.py`: FastAPI app factory
   `create_app(pipeline, provider="openai")` with `GET /health` and
   `POST /ask` (builds the Phase 5 graph once at app-creation time, not
   per request).
3. Added `backend/notebooks/12_api_services.ipynb`: built one shared
   `RetrievalPipeline` pointed at an *empty* collection, exercised the
   Flask app via `app.test_client()` and the FastAPI app via
   `fastapi.testing.TestClient` — both in-process, never as two live
   servers.
4. Result — both services worked exactly as designed, verified with real
   calls:
   - `GET /health` on both returned `{"status": "ok"}`.
   - `POST /ingest` with a real uploaded PDF returned `{"chunks": 4}`, and
     actually populated the shared collection (not a stub response).
   - `POST /ask` with the usual grounded question, run through the real
     Phase 5 graph against that freshly-ingested collection, returned
     `{"answer": "...(page 1)...(page 4)...", "grounded": true,
     "pages": ["1", "4"]}` — i.e. the full ingest → ask round trip works
     over HTTP request/response shapes, not just in a notebook variable.
5. Didn't test: two separate OS processes (`flask run` + `uvicorn`) hitting
   the same local-mode Qdrant path at the same time. As predicted in "Why
   this way", that's expected to fail on the file lock — not attempted
   here on purpose, since the fix is Qdrant server mode in Phase 11, not
   something to paper over now.
