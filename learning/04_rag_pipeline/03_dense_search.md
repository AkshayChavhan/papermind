# 03 — Dense vector search / retrieval

## What's about to happen

This is Phase 2 · Step 3. Step 2 filled the collection with chunk vectors;
this step finally searches it:

1. Take a plain-English question.
2. Embed that question with the *same* model used for the chunks
   (`BAAI/bge-small-en-v1.5`) — a query and a chunk only compare meaningfully
   if they're turned into numbers the same way.
3. Ask Qdrant for the chunks whose vectors are closest to the question's
   vector (top-k).
4. Print each result's text, `page_label`, and similarity score, and sanity
   check that the top result is actually relevant to the question.

## Why this way

**`query_points`, not the older `search` method**
`qdrant-client` 1.20 still has `.search()` for backwards compatibility, but
`.query_points()` is the current recommended API — same idea (nearest
vectors), but it's what later steps (hybrid search, re-ranking) build on
too, so starting with it now avoids a rewrite in Step 4/5.

**Same embedding model for the query as for the chunks**
Cosine similarity only makes sense between vectors produced the same way.
Using a different model (or even a different version of the same model)
for the query would put it in a different "meaning space" than the stored
chunks, making every comparison meaningless.

**top_k = 2, with a manual relevance check — no automated metric yet**
With only 4 sample chunks, 2 is enough to see both "a good match" and "a
worse match" side by side. A real precision/recall metric belongs to
Phase 7 (Evaluation) once there's a bigger, labeled test set — here we're
just confirming the plumbing works end to end.

## Diagram

```
 "How is citation accuracy measured?"  (plain English question)
         │
         ▼  fastembed (same model as the chunks)
   384-dim query vector
         │
         ▼  client.query_points(collection, vector, limit=2)
 ┌─────────────────────────────┐
 │ result 1: page 3, score 0.82 │  <- "Results" chunk, most relevant
 │ result 2: page 1, score 0.54 │  <- "Abstract" chunk, loosely related
 └─────────────────────────────┘
```

## What we did

1. Added `backend/notebooks/04_dense_search.ipynb`:
   - Connected to the existing `papermind_chunks` collection (4 points, from
     Step 2).
   - Asked: *"How is citation accuracy measured in this paper?"* — embedded
     it with the same `BAAI/bge-small-en-v1.5` model used for the chunks.
   - Ran `client.query_points(..., limit=2)`.
2. Result: top match was page 4 ("3. Results" — the section that actually
   discusses citation accuracy being rated by human reviewers), score 0.693.
   Second match was page 1 (the Abstract, which also mentions citation
   accuracy in passing), score 0.657. Both scores are close because the
   sample PDF is tiny and every page is about the same overall topic — with
   a real, longer paper the gap between a direct hit and a loose match
   would be larger.
3. The sanity-check assertion (top result mentions "citation" or is the
   Results page) passed — confirms the embed → store → search loop works
   end to end before building anything more on top of it.
