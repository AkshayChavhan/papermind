# 04 — Hybrid search (dense + keyword/sparse)

## What's about to happen

This is Phase 2 · Step 4. Step 3 proved dense (meaning-based) search works.
This step adds a second, complementary kind of search — keyword/sparse — and
combines both into one ranking:

1. Recreate `papermind_chunks` with **two** vector types per point instead
   of one: a `dense` vector (what we already had) and a `bm25` sparse
   vector (new).
2. Re-embed every chunk with both and upsert them.
3. Search by embedding the question both ways too, then let Qdrant fuse the
   two rankings into a single result list.

No new PDF, no new chunks — same 4 chunks as before, just stored with an
extra vector each.

## Why this way

**Why hybrid at all?**
Dense search compares *meaning* — great for "what's this about," weak for an
exact term (a model name, a number, an acronym) that a chunk uses but that
isn't the dominant "meaning" of the sentence. Sparse/keyword search (BM25)
is the opposite: it matches exact words well but doesn't understand
synonyms or paraphrasing. Combining both catches more of what a real
question needs than either alone.

**Sparse method: BM25 via `fastembed`'s `Qdrant/bm25`, not a neural sparse
model**
BM25 is the same classic, deterministic keyword-ranking algorithm search
engines have used for decades — no model weights to download beyond a
tokenizer, no training, nothing to go wrong in a surprising way. `fastembed`
ships it as a drop-in `SparseTextEmbedding`, consistent with Step 1's
decision to prefer fastembed over heavier libraries. Neural sparse models
(SPLADE, BM42) exist and can do better in some cases, but they're a
tune-later upgrade, not a starting point.

**Recreating the collection, not altering it in place**
Qdrant collections are empty of named vectors you decide once, like
`requirements.txt` fixes versions once on install. Switching from "one
unnamed dense vector" (Step 1) to "a *named* dense vector plus a *named*
sparse vector" changes that fixed shape, so there's no in-place upgrade —
only recreate-and-reload. That's cheap here: the 4 chunks regenerate from
`generate_sample_pdf.py` in under a second, and the `uuid5` IDs from Step 2
make the reload idempotent either way.

**Combining rankings with Reciprocal Rank Fusion (RRF), not a manual score
blend**
Dense similarity scores (cosine, 0–1) and BM25 scores (unbounded, depends on
term rarity) aren't on the same scale, so adding or averaging them directly
is meaningless. RRF sidesteps that entirely — it only looks at each
result's *rank* in each list, not its raw score, and combines those ranks.
It's Qdrant's built-in, recommended way to do this (`FusionQuery(fusion=RRF)`
over two `Prefetch` queries), so no custom scoring logic is needed.

## Diagram

```
 chunk text
    ├──> fastembed TextEmbedding (dense, 384-dim)  ──┐
    └──> fastembed SparseTextEmbedding "bm25" ───────┤
                                                       ▼
                               PointStruct(vector={"dense": ..., "bm25": ...})
                                                       │
                                                       ▼
                              papermind_chunks (recreated, 2 named vectors)

 question ──> embed both ways ──> Prefetch(dense) + Prefetch(bm25)
                                            │
                                            ▼
                                   FusionQuery(RRF)
                                            │
                                            ▼
                                    combined top-k results
```

## What we did

1. Added `backend/notebooks/05_hybrid_search.ipynb`:
   - Recreated `papermind_chunks` with `vectors_config={"dense": ...}` and
     `sparse_vectors_config={"bm25": SparseVectorParams(modifier=Modifier.IDF)}`.
   - Embedded all 4 chunks with both `TextEmbedding` (dense) and
     `SparseTextEmbedding("Qdrant/bm25")` (sparse) — confirmed dim=384 for
     dense, and a handful of non-zero BM25 terms per chunk for sparse.
   - Upserted points with `vector={"dense": ..., "bm25": SparseVector(...)}`,
     same `uuid5` IDs and payload as Step 2.
   - Searched with the same question as Step 3, using two `Prefetch`
     queries (dense + bm25) fused with `FusionQuery(fusion=Fusion.RRF)`.
2. Result: the top two results were the same two pages as Step 3's
   dense-only search (page 4 "Results", page 1 "Abstract") — but with
   **tied** RRF scores (0.833 each). That's an artifact of this dataset
   being only 4 chunks: with so few candidates, both the dense and sparse
   rankings put these same two chunks in their respective top 2, so RRF
   (which only looks at rank position, not raw score) produces identical
   combined scores. A larger, more varied document set would show RRF
   actually separating cases where dense and sparse disagree — this sample
   is too small to demonstrate that, but the mechanism itself (fuse two
   rankings into one) is confirmed working correctly.
3. The sanity-check assertion (a citation-mentioning chunk is in the
   results) passed.
