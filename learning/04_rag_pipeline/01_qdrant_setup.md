# 01 — Qdrant local mode + collection

## What's about to happen

This is Phase 2 · Step 1. The chunks from Step 2 of Phase 1 need somewhere
to live once they're turned into vectors (Phase 2 · Step 2). This step:

1. Installs `qdrant-client` and gets Qdrant running in **local mode** — no
   server, no Docker (this was already decided in
   [ARCHITECTURE.md](../../docs/ARCHITECTURE.md)).
2. Picks the embedding model now, even though embedding itself is Step 2 —
   a collection has to be created with a fixed vector size, and that size
   comes from the model.
3. Creates a collection sized for that model, in a notebook, and confirms it
   exists.

## Why this way

**Qdrant "local mode", not a Docker server**
Already decided in ARCHITECTURE.md. `qdrant-client` can run Qdrant's engine
embedded in the Python process, persisting to a folder on disk — same
behavior as venv in Phase 1 Step 1: zero extra install, nothing new to run
or manage. If the project ever needs a shared/remote Qdrant, the same client
code points at a URL instead of a local path — swapping later costs nothing.

**Embedding library: `fastembed`, not `sentence-transformers`**
`sentence-transformers` pulls in PyTorch — a multi-GB dependency that's
overkill for this project's needs. `fastembed` is Qdrant's own embedding
library: ONNX-based, lightweight, CPU-fast, and built to pair directly with
`qdrant-client`. No paid API, no heavy install.

**Model: `BAAI/bge-small-en-v1.5` (384 dimensions)**
A small model specifically benchmarked for retrieval/RAG (not general text
similarity), good quality for its size, and free — keeping Phase 2 cost-free
before Phase 3 introduces paid LLM APIs.

**Distance metric: Cosine**
The standard pairing for BGE-style (normalized) embeddings — nearly every
sentence-embedding model is compared this way.

## Diagram

```
 backend/notebooks/data/qdrant/        <- NEW, local on-disk storage (gitignored)
         ▲
         │  QdrantClient(path=...)
         │
 ┌───────────────────────────┐
 │ collection: papermind_chunks│
 │  vector size: 384           │
 │  distance: Cosine           │
 └───────────────────────────┘
         │
         ▼ (Phase 2 · Step 2 fills this with real chunk vectors)
```

## What we did

1. Installed the new packages into `backend/.venv`:
   ```
   cd backend
   source .venv/bin/activate
   pip install qdrant-client fastembed
   ```
   `requirements.txt` now also pins `qdrant-client` and `fastembed`.
2. Confirmed `fastembed`'s `BAAI/bge-small-en-v1.5` model reports 384
   dimensions — that's the number the collection needs to match.
3. Added `backend/notebooks/02_qdrant_setup.ipynb`:
   - Opens a local-mode client: `QdrantClient(path="data/qdrant")` (gitignored,
     same pattern as the Phase 1 · Step 2 sample PDF).
   - Creates collection `papermind_chunks` with `vector size=384`,
     `distance=Cosine`.
   - Confirms it exists, and reports `points_count: 0` (nothing stored yet —
     that's Step 2's job).
4. Ran the notebook in place (`jupyter nbconvert --execute`) so it's
   committed with real output.
