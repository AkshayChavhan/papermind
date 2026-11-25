# 02 — Prompt v2 (citation/grounding instructions)

## What's about to happen

v1 confirmed the hypothesis: a prompt with no citation instruction never
cites pages, even though `page_label` is sitting right there in the chunk
metadata. v2 fixes exactly that one thing — nothing else — so the
before/after comparison stays clean:

1. Each chunk is now labeled with its page number *inside the prompt text*
   (v1 just concatenated raw chunk text with no labels at all).
2. The instruction changes from "answer the question using the context
   above" to an explicit rule: answer using only the context, and cite the
   page number for every claim, e.g. `(page 4)`.
3. Still **no** refuse-if-not-grounded rule yet — that's v3. If v2's answer
   makes something up with a confident-looking citation, that's useful
   information for why v3 is needed, not something to patch here.

## Why this way

**One change at a time**
v1 → v2 only changes two things: chunks are labeled with their page number,
and the instruction asks for citations. Everything else (model, chunks,
question, retrieval) stays identical to v1's run so the comparison isolates
the effect of the prompt change, not some other variable.

**Labeling chunks is required, not optional**
The model can't cite "(page 4)" if the text it's given doesn't say which
page it came from. v1's `build_prompt` joined `chunk["text"]` directly; v2
has to join `f"(page {chunk['page_label']})\n{chunk['text']}"` instead, or
the citation instruction has nothing to point at.

**Still same question + same two chunks as v1**
Reusing the exact question ("How is citation accuracy measured in this
paper?") and the same reranked top-2 chunks (page 1 Abstract, page 4
Results) from notebook 08 means the v1 vs v2 answers are directly
comparable side by side in the v3 notebook later, not comparing apples to
oranges.

## Diagram

```
 question ──┐
            ▼
 Phase 2 pipeline (hybrid search + re-rank) ──> top-k chunks
            │
            ▼
 backend/src/prompts/v2.py
   build_prompt(question, chunks) ──>
     "Context:\n(page 1)\n...\n\n(page 4)\n...\n\nQuestion: ...\n\n
      Answer using only the context above. Cite the page number for
      every claim, e.g. (page 4)."
            │
            ▼
   answer(question, chunks, llm) ──> llm.invoke(prompt) ──> answer with
                                       inline page citations (hopefully)
            │
            ▼
   notebook: run v1 and v2 side by side on the same question/chunks,
   compare manually — does v2 actually cite pages now?
```

## What we did

1. Added `backend/src/prompts/v2.py`: `build_prompt` now labels each chunk
   with `(page {page_label})` before its text, and the instruction tells the
   model to answer using only the context and cite the page number for
   every claim.
2. Added `backend/notebooks/09_prompt_v2.ipynb`: same pipeline, same
   question, same two reranked chunks (page 1 Abstract, page 4 Results) as
   notebook 08, run through both `v1.answer` and `v2.answer` back to back
   for a direct comparison.
3. Result — v2 does exactly what it was asked to do:
   - v1 (re-run here for comparison): no page citations anywhere in the
     answer, same as before.
   - v2: *"...combining dense retrieval with a re-ranking stage improves
     citation accuracy compared to retrieval alone **(page 1)**. ...
     grounded answers with page citations were rated as more trustworthy
     than ungrounded answers by human reviewers **(page 4)**..."* — both
     citations are correct (the claims really do come from those pages).
   - Neither version invents an answer to "how is citation accuracy
     measured" (the paper never actually says), but v2's version is now
     traceable back to a source page per claim, which v1's wasn't. That's
     the whole point of v2.
4. v2 doesn't yet handle the case where the context has *nothing* relevant
   at all — it would likely still produce a prose answer with no
   citations rather than explicitly refusing. That's exactly what v3 adds
   next.
