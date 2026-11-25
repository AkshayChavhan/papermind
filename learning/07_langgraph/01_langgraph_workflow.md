# 01 — Phase 5: LangGraph workflow (retrieve → grade → generate → verify → not-found)

## What's about to happen

Every piece built so far (hybrid search + re-rank in Phase 2, `get_llm()`
in Phase 3, prompt v1/v2/v3 in Phase 4) has lived inside notebook cells,
called one function at a time, with a human reading the output and
deciding what it means. Phase 5 wires those pieces into one actual
decision-making pipeline using LangGraph, so answering a question becomes
a single `graph.invoke({"question": ...})` call instead of a notebook
walkthrough:

```
retrieve --> grade --(relevant?)--> generate --> verify --(grounded?)--> done
                 \                                  \
                  --> not_found (no relevant chunks)  --> not_found (ungrounded answer)
```

- **retrieve**: hybrid search + re-rank (unchanged from Phase 2) over the
  question.
- **grade**: an LLM call that judges, yes/no, whether the retrieved chunks
  are actually relevant to the question at all — a *before-generation*
  gate, separate from prompt v3's refusal (which happens *after*
  generation, inside the answer text itself).
- **generate**: prompt v3 (the most defensive version from Phase 4) builds
  the prompt and calls the LLM.
- **verify**: a cheap, code-only check — not another LLM call — on the
  generated answer: does it actually contain a page citation like
  `(page N)`? If not, either the question wasn't grounded in the context,
  or v3's refusal kicked in and said so in prose.
- **not_found**: a single fixed message, reached from either gate, so the
  app always has one predictable "I don't know" response instead of N
  different ways of saying it.

## Why this way

**Two different checks, not one, and that's deliberate**
`grade` and `verify` look similar (both are "is this good enough?"
checks) but they protect against different failure modes:
- `grade` catches *bad retrieval* — hybrid search returning only
  loosely-related chunks for a question way outside the document's scope.
  Nothing has been generated yet, so this is cheap to short-circuit.
- `verify` catches *bad generation* — even with decent chunks, the model
  could still answer without a citation (prose with no `(page N)`
  anywhere), which is exactly the failure v1 showed in task #11 before any
  prompt engineering existed. This is a real, lightweight grounding check,
  not just trusting the prompt to have worked.

Task #13's finding (gpt-4o-mini already refuses cleanly on fully
unrelated context, but v3 can under-cite on partially-grounded questions)
is why both gates exist instead of relying on prompt wording alone — the
graph is meant to catch model behavior the prompt doesn't fully control,
not just copy what v3 already does.

**`verify` is code, not another LLM call, by design**
A citation-presence check (`"(page" in answer`) is deterministic, free,
and fast. Task #16 (formal evaluation — RAGAS/TruLens/custom citation
metric) is exactly where a more sophisticated, possibly LLM-based
groundedness check belongs. This graph's `verify` node is intentionally
the simplest thing that catches the specific failure mode seen so far
(no citation at all), not a preview of Phase 7.

**Retrieval logic finally moves into `backend/src/retrieval/`**
Notebooks 06/08/09/10 each duplicated the same hybrid-search-then-rerank
code inline — fine while nothing but a notebook called it. Phase 5 is the
first time retrieval needs to be *called from code*, not read from a
printed cell, so it becomes `backend/src/retrieval/pipeline.py`'s
`RetrievalPipeline` class, wrapping the embedders/reranker/Qdrant client
so they're loaded once and reused across every node call instead of
reloading expensive models per question.

**One LangGraph `StateGraph`, state as a `TypedDict`**
Matches the stack decision in `ARCHITECTURE.md` (LangGraph is the chosen
orchestration layer, same as LangChain's `get_llm()` from Phase 3). State
carries `question`, `chunks`, `answer`, and `grounded` between nodes —
nothing more, since nothing else is needed yet (e.g. no conversation
history — this is single-question Q&A, matching the app's scope so far).

## Diagram

```
                     ┌────────────┐
   question ───────> │  retrieve  │  hybrid search + re-rank (Phase 2)
                     └─────┬──────┘
                           ▼
                     ┌────────────┐
                     │   grade    │  LLM: are these chunks relevant at all?
                     └─────┬──────┘
                 relevant? │  not relevant
                 ┌─────────┴─────────┐
                 ▼                   ▼
           ┌────────────┐      ┌────────────┐
           │  generate  │      │ not_found  │ ──> END
           └─────┬──────┘      └────────────┘
                 ▼
           ┌────────────┐
           │   verify   │  code: does the answer contain "(page N)"?
           └─────┬──────┘
         grounded │  not grounded
         ┌────────┴────────┐
         ▼                 ▼
       END            not_found ──> END
```

## What we did

1. Added `backend/src/retrieval/pipeline.py`'s `RetrievalPipeline`: wraps
   the dense/sparse embedders, cross-encoder reranker and Qdrant client
   from Phase 2, with `ingest(pdf_path)` and `retrieve(question)` methods,
   replacing the inline-duplicated code notebooks 06/08/09/10 each had.
2. Added `backend/src/graph/workflow.py`'s `build_graph(pipeline, llm)`:
   a `StateGraph` with `retrieve` → `grade` → (conditional) `generate` →
   `verify` → (conditional) `not_found`/END, exactly matching the diagram
   above.
3. Added `backend/notebooks/11_langgraph_workflow.ipynb`: built the graph
   with real `RetrievalPipeline` + `get_llm("openai")`, then ran 3 real
   questions through `graph.invoke(...)`.
4. Results — 2 of 3 as expected, 1 more interesting than expected:
   - **Case 1 (grounded question)**: `grade` passed it through, `generate`
     produced an answer citing both `(page 1)` and `(page 4)`, `verify`
     confirmed `grounded: True`. Full pipeline worked end to end exactly
     as designed.
   - **Case 2 (totally off-topic — "capital of France")**: only one LLM
     call happened (the `grade` call) before the graph routed straight to
     `not_found` — `generate`/`verify` never ran. Exactly as designed.
   - **Case 3 (topically close but ungrounded — "funding source")**: also
     only one LLM call happened. `grade` judged the retrieved chunks *not*
     relevant and routed straight to `not_found`, the same as case 2.
   - **Honest gap this surfaced**: `grade` turned out stricter than
     expected — in task #13, this exact question reached `generate` and
     produced an uncited refusal from every prompt version. Here, `grade`
     filtered it out *before* generation, which means `verify`'s citation
     check (the second safety net, meant to catch exactly this kind of
     case) never actually got exercised in this run. The two-gate design
     is still reasonable — `grade` being stricter is not a bug, it's one
     possible LLM judgment on one borderline question — but this notebook
     hasn't yet produced a case that proves `verify` catches something
     `grade` misses. That's a known gap to close with a wider or repeated
     test (ideally as part of task #16's formal evaluation), not something
     fixed here by tweaking the test until it says what was expected.
