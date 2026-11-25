# 01 — Prompt v1 (baseline RAG prompt)

## What's about to happen

Phase 3 gave us `get_llm()` — a way to call an LLM. Phase 4 connects that to
the actual retrieval pipeline from Phase 2: take a question, retrieve +
re-rank chunks, stuff them into a prompt, and get an answer back. This is
the first of 3 versions (v1 → v2 → v3), each one fixing a weakness the
previous version exposes:

1. **v1 (this task)**: the simplest possible RAG prompt — dump the
   retrieved chunk text into the prompt, ask the question, no instructions
   about citing sources or refusing to answer. A deliberately naive
   baseline.
2. v2 (next task) adds citation/grounding instructions.
3. v3 (after that) adds a refuse-if-not-grounded rule, and all three get
   compared side by side on the same questions.

## Why this way

**Starting naive on purpose**
The point of having a v1 at all is to see, concretely, what goes wrong
without any prompt engineering — not to assume it. If v1 already cited
pages correctly by accident, that would be useful to know too. Either way,
v2 and v3 are justified by what v1 actually does, not by guessing ahead of
time what an LLM "probably" needs to be told.

**Prompt logic lives in `backend/src/prompts/`, not the notebook**
Same reasoning as Phase 3's `get_llm()`: Phase 5 (LangGraph workflow) will
call whichever prompt version wins this comparison, so the prompt-building
+ answering logic needs to be an importable function, not something typed
only into a notebook cell. `backend/src/prompts/v1.py` holds it; the
notebook calls it and inspects the result.

**No citation/grounding instructions yet, by design**
v1's prompt template is literally "here's context, here's a question,
answer it" — nothing about page numbers, nothing about refusing when the
context doesn't cover the question. That's the whole point of calling it
v1: it's the control to compare v2/v3 against.

## Diagram

```
 question ──┐
            ▼
 Phase 2 pipeline (hybrid search + re-rank) ──> top-k chunks
            │
            ▼
 backend/src/prompts/v1.py
   build_prompt(question, chunks) ──> "Context:\n...\n\nQuestion: ...\n\nAnswer..."
            │
            ▼
   answer(question, chunks, llm) ──> llm.invoke(prompt) ──> plain-text answer
            │
            ▼
   notebook: print answer, manually check — does it cite pages? does it
   make anything up?
```

## What we did

1. Added `backend/src/prompts/v1.py`: `build_prompt(question, chunks)`
   joins chunk text with no page labels, `answer(question, chunks, llm)`
   formats the prompt and calls `llm.invoke(...)`.
2. Added `backend/notebooks/08_prompt_v1.ipynb`: rebuilt the Phase 2
   pipeline (hybrid search, limit=4, re-ranked down to top 2), then ran
   those 2 real chunks (page 1 "Abstract", page 4 "3. Results") through
   `answer_v1` with the real OpenAI call from Phase 3.
3. Result, as expected: the answer was reasonable prose, but **never
   mentioned a page number or which chunk anything came from** — e.g. "the
   context does not provide specific details on how citation accuracy is
   measured... it indicates that the improvement in citation accuracy is
   assessed by comparing..." with no "(page 4)" or similar anywhere. This
   confirms the hypothesis behind having a v1 at all: a prompt with no
   citation instruction simply doesn't produce citations, even though the
   underlying chunk metadata (`page_label`) is sitting right there, just
   unused by the prompt. v2 adds the instruction to actually use it.
