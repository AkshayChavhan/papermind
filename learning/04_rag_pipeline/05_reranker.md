# 05 — Re-ranker on top of hybrid results

## What's about to happen

This is Phase 2 · Step 5, the last step of Phase 2. Step 4 fused dense +
BM25 into one ranked list. This step adds a second pass on top of that
list:

1. Run hybrid search same as Step 4, but pull back more candidates than we
   actually need (e.g. top 4 instead of top 2) — a wider net.
2. Feed the question and each candidate's text into a cross-encoder
   re-ranker, which scores how well each one actually answers the question.
3. Re-sort by that score and keep the real top-k. That final list is what
   would be handed to the LLM in Phase 3.

No new PDF, no new chunks, no change to the Qdrant collection — re-ranking
only touches the already-retrieved candidates, after they come back from
Qdrant.

## Why this way

**Why re-rank at all, if hybrid search already ranks everything?**
Dense + BM25 are both *fast, approximate* — they score a question against
each chunk independently and cheaply, which is what makes them fast enough
to run over thousands of chunks. A cross-encoder re-ranker is *slow but
precise* — it reads the question and a candidate chunk together, as one
input, so it can judge their relationship directly instead of comparing two
separately-computed vectors. That's too slow to run over every chunk in a
collection, but cheap enough to run over the dozen or so candidates hybrid
search already shortlisted. Retrieve wide and cheap, then re-rank narrow
and precise.

**Cross-encoder model: `Xenova/ms-marco-MiniLM-L-6-v2` via fastembed's
`TextCrossEncoder`, not a separate library**
Same reasoning as Steps 1 and 4: fastembed already ships this as a small
(~80MB), ONNX-based, no-GPU-needed model purpose-built for re-ranking
question/passage pairs — consistent with preferring fastembed over heavier
libraries (e.g. `sentence-transformers` cross-encoders) throughout this
project. No new package, no new line in `requirements.txt`.

**Over-fetch before re-ranking**
If hybrid search only returned the final top-k, there'd be nothing left for
the re-ranker to correct — it can only promote a result that was retrieved
but ranked lower. So Step 5 asks Qdrant for more candidates (top 4, all 4
of our sample chunks) than the final answer needs (top 2), and lets the
re-ranker pick the best 2 out of those 4.

## Diagram

```
 question ──> hybrid search (Step 4), limit=4  ──> 4 candidate chunks
                                                          │
                      for each candidate: (question, chunk text)
                                                          ▼
                        TextCrossEncoder("Xenova/ms-marco-MiniLM-L-6-v2")
                                                          │
                                                          ▼
                                 re-rank score per candidate
                                                          │
                                                          ▼
                                  sort, keep top-k (final answer)
```

## What we did

1. Added `backend/notebooks/06_reranker.ipynb`:
   - Rebuilt the hybrid-search collection exactly as Step 4 did, then ran
     the same question with `limit=4` instead of 2 — RRF order: page 4
     and page 1 tied at 0.833, then page 3 (0.250), then page 2 (0.200).
   - Re-ranked those 4 candidates with `TextCrossEncoder("Xenova/ms-marco-MiniLM-L-6-v2")`,
     took the top 2 by re-rank score.
2. Result, and an honest surprise: the re-ranker **reversed** the order of
   the top two candidates versus Step 4. RRF (tied) had put page 4
   ("3. Results") first; the cross-encoder scored page 1 (the Abstract,
   2.993) clearly above page 4 (−3.928). Looking at the actual text, the
   Abstract literally contains the phrase "citation accuracy" — an almost
   verbatim match to the question — while the Results page talks about
   citations and trustworthiness without that exact phrase. The
   cross-encoder is reading the question and each chunk together as one
   input, so a close wording match like this can outweigh a chunk that's
   topically about the right section. That's expected cross-encoder
   behavior, not a bug — it's also a reminder that a reranker's job is to
   judge relevance by its own learned criteria, which won't always agree
   with what a human skimming the section headers would guess first. The
   sanity check was kept lenient (just checks a citation-mentioning chunk
   is somewhere in the final results) for the same reason Step 4's was:
   with 4 sample chunks there isn't a large enough test set to assert one
   "correct" order.
3. Confirmed no new dependency was needed — `fastembed` 0.9.1 (already
   pinned from Step 1) ships `TextCrossEncoder` out of the box.
