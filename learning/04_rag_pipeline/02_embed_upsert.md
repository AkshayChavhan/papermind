# 02 — Embed chunks + upsert into Qdrant

## What's about to happen

This is Phase 2 · Step 2. Step 1 built an empty collection; this step fills
it:

1. Reloads and re-chunks the sample PDF the same way
   `backend/notebooks/01_pdf_ingestion.ipynb` did (duplicated inline — there's
   no shared `backend/src/` module yet, so every notebook so far is
   self-contained).
2. Turns each chunk's text into a 384-number vector with `fastembed`.
3. Builds one point per chunk (vector + a small payload) and upserts them
   into the `papermind_chunks` collection from Step 1.
4. Verifies the write landed correctly — no search yet, that's Step 3.

## Why this way

**Reusing notebook 01's loading/chunking code inline, not importing it**
Nothing outside notebooks exists yet to import from. Pulling this into a
shared module is deferred until something other than a notebook actually
needs it (likely Phase 6's backend services).

**Point ID: deterministic, not random**
Qdrant's `upsert` is "insert, or replace if the ID already exists." A random
ID would mean running this notebook twice creates duplicate points for the
same chunks. Instead each point's ID is a `uuid5` built from
`file_name:page_label:chunk_index` (`chunk_index` resets per page, since a
page can produce more than one chunk) — the same chunk always gets the same
ID, so re-running this notebook overwrites instead of duplicating. Qdrant
requires an ID to be an unsigned int or a UUID, which is why it's a UUID and
not just that string directly.

**Payload: `text`, `page_label`, `file_name`, `chunk_index` — nothing more**
`text` lets us (and later, citations) see what was actually stored without
decoding the vector. `page_label` is the citation page number. `file_name`
future-proofs for more than one PDF sharing this collection. `chunk_index`
mirrors the ID and is useful for debugging. No scores or timestamps yet —
add fields only once something actually needs them.

**Verifying with a count + a direct lookup, not a search**
`points_count == len(nodes)` confirms every chunk landed exactly once.
Retrieving one point by ID and printing its payload/vector confirms the
shape is right. Actual semantic search is Step 3's job, kept out of scope
here.

## Diagram

```
 nodes (chunks, from notebook 01)
         │
         ▼  fastembed: TextEmbedding("BAAI/bge-small-en-v1.5")
   384-dim vectors
         │
         ▼  PointStruct(id=uuid5(...), vector, payload)
┌───────────────────────────────┐
│ papermind_chunks (populated)   │
│  point: {page_label, file_name,│
│          chunk_index, text}    │
└───────────────────────────────┘
         │
         ▼
 (Phase 2 · Step 3 will query this collection)
```

## What we did

1. Added `backend/notebooks/03_embed_upsert.ipynb`:
   - Reloaded + re-chunked the sample PDF exactly as notebook 01 does →
     `nodes` (4 chunks from 4 pages).
   - Connected to the existing `papermind_chunks` collection from notebook 02
     (asserted it already exists rather than recreating it).
   - Embedded all 4 chunks with `TextEmbedding("BAAI/bge-small-en-v1.5")` →
     confirmed `dim=384`, matching the collection.
   - Built one `PointStruct` per chunk with a `uuid5`-derived ID and the
     planned payload (`text`, `page_label`, `file_name`, `chunk_index`), then
     `client.upsert(...)`.
   - Verified: `points_count == 4` (matches chunk count), and a direct
     `retrieve()` on one point showed the expected payload and a 384-length
     vector.
2. Ran the notebook in place (`jupyter nbconvert --execute`) twice in a row
   and confirmed `points_count` stayed at 4 both times, with the same point
   ID reappearing — the uuid5 scheme makes re-running idempotent (overwrite,
   not duplicate), as intended.
3. Caught and fixed one bug while running it: `client.retrieve(...)` needs
   `collection_name` as an explicit argument — it's not inferred from the
   client the way `get_collection` is.
