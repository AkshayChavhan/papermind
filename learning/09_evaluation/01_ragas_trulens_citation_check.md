# 01 — Phase 7: Evaluation (RAGAS, TruLens, custom citation check)

## What's about to happen

Every check so far — tasks #11–#15 — has been a human (me, writing the
learning doc) reading one or two printed answers and judging them by eye.
That doesn't scale past a handful of examples, and it's exactly the
limitation flagged repeatedly: task #13 called out that a single manual
read can't separate real signal from gpt-4o-mini's run-to-run variance;
task #14 flagged that `verify`'s citation check was never actually
exercised by the 3 manual test cases. Phase 7 replaces "read the answer
and judge it" with three real, repeatable scores, run over a small but
varied eval set (grounded / off-topic / topically-close-but-ungrounded —
the same categories used informally since task #13):

1. **RAGAS faithfulness** — does the generated answer's claims actually
   follow from the retrieved context? (library metric, LLM-graded)
2. **TruLens groundedness** — a second, independent library's version of
   the same question, to see whether the two libraries agree.
3. **Custom citation-precision metric** — code-only, deterministic: of
   the page numbers the answer actually cites, what fraction correspond
   to a chunk that was really retrieved? Catches a specific failure mode
   neither RAGAS nor TruLens targets directly: a confident-sounding but
   *wrong* citation (e.g. `(page 7)` when page 7 was never retrieved).

## Why this way

**Two different libraries, not one, on purpose**
RAGAS and TruLens are both "LLM judges the answer" tools, but they're
independent implementations with different prompts and scoring
conventions. Running both on the same eval set is itself a mini
experiment: if they agree, that's more trustworthy than either alone; if
they disagree, that's worth knowing about *before* trusting either one to
gate anything in Phase 8/beyond.

**The custom metric exists because neither library checks citations
specifically**
RAGAS/TruLens faithfulness-style metrics judge semantic entailment
("is this claim supported by the context"), not whether a *page number*
printed in the text is one of the pages actually retrieved. Prompt v2/v3
ask the model to cite real page numbers; nothing so far has verified the
model doesn't just make up a plausible-looking `(page N)`. That's a
narrow, code-only check — `backend/src/evaluation/citation_check.py`'s
`citation_precision(answer, chunks)` — deliberately simple so it's a
clear signal, not another LLM judgment layered on top of two others.

**Reusing the same eval questions as tasks #13/#14, plus one new grounded
one**
The grounded/off-topic/ungrounded split proved useful for exposing real
behavior (task #14's `grade`-vs-`verify` gap). Reusing those exact
questions means this task's scores are comparable to what was already
observed by hand, rather than a fresh, uncalibrated set. One new grounded
question (about chunking method, page 3) is added purely to check that
"grounded" isn't a fluke of one specific question/page pair.

**Scores recorded and read honestly, not used to gate anything yet**
This task computes and reports scores; it does not wire a pass/fail
threshold into the LangGraph workflow. That would be a real, separate
design decision (what threshold, what happens on failure) better made
once there's more than one notebook's worth of data to calibrate against.

## Diagram

```
  eval questions (4: grounded x2, off-topic, ungrounded)
            │
            ▼
  Phase 5 graph.invoke({"question": ...})  --> chunks, answer, grounded
            │
   ┌────────┼─────────────────────┐
   ▼        ▼                     ▼
 RAGAS    TruLens          citation_precision(answer, chunks)
 Faithfulness  groundedness   (code-only: cited pages ⊆ retrieved pages?)
   │        │                     │
   └────────┴─────────────────────┘
                   │
                   ▼
   printed table: question | ragas | trulens | citation_precision
   (read honestly — do the three scores agree? where do they diverge?)
```

## What we did

1. Added `backend/src/evaluation/citation_check.py`'s
   `citation_precision(answer, chunks)`: regex-extracts `(page N)`
   citations from the answer, returns the fraction that match an actually
   retrieved chunk's `page_label`, or `None` if the answer has no
   citations at all.
2. Added `backend/notebooks/13_evaluation.ipynb`: ran 4 questions through
   the real Phase 5 graph, then scored each result with RAGAS
   `Faithfulness`, TruLens `groundedness_measure_with_cot_reasons`, and
   `citation_precision` — 3 independent judgments per answer.
3. Installed `ragas==0.4.4` and `trulens==2.16.0` /
   `trulens-providers-openai==2.16.0`. `ragas` pulled in its own
   `langchain-openai` requirement, which downgraded the pin from `1.8.5`
   (task #10) to `1.1.9` — re-verified `get_llm("openai").invoke(...)`
   still works correctly after the downgrade before moving on.
4. Results — genuinely surprising, and worth recording exactly as
   observed rather than smoothed over:

   | question | grade result this run | ragas faithfulness | trulens groundedness | citation precision |
   |---|---|---|---|---|
   | grounded_citations | **not relevant** (refused) | 0.00 | 1.00 | None |
   | grounded_chunking | relevant → generated, cited (page 2)/(page 3) | 1.00 | 0.83 | **1.0** |
   | offtopic | not relevant (refused) | 1.00 | 1.00 | None |
   | ungrounded_funding | not relevant (refused) | 0.00 | 1.00 | None |

   - **`grade` is non-deterministic across runs, confirmed again**: the
     exact same "How is citation accuracy measured?" question that task
     #14's notebook 11 graded as relevant (and which generated a
     correctly-cited answer) was graded **not relevant** this run,
     short-circuiting straight to the refusal message instead. This is
     the same gpt-4o-mini run-to-run variance flagged in task #13, now
     shown affecting the `grade` gate specifically, not just `generate`.
   - **RAGAS scored the literal same refusal string 0.0, 1.0, and 0.0**
     across the three refused questions — the exact text
     "I don't have enough information in the uploaded document to answer
     that." got three different faithfulness scores depending only on
     which (irrelevant) chunks were in context. That's a real limitation
     of using an LLM-judged faithfulness metric on refusal-type answers,
     not a bug in this project's code — RAGAS's prompt is reasoning about
     whether the statement's (absence of) claims are supported by that
     specific context, and that reasoning isn't stable. Trusting a single
     faithfulness number on a refusal would be misleading.
   - **TruLens groundedness was uniformly high (0.83–1.0) regardless of
     relevance or correctness**, including for the off-topic refusal.
     This matches the metric's actual definition — "does the statement
     avoid unsupported claims" — which a short refusal trivially
     satisfies. It is not measuring citation correctness at all.
   - **The custom citation-precision metric was the one score that
     behaved exactly as designed**: `None` for every answer with no
     citation (all 3 refusals), and a clean `1.0` for the one real
     generated-and-cited answer, where the model cited pages 2 and 3 and
     both were genuinely among the retrieved chunks. This is direct
     empirical confirmation of the "Why this way" rationale — neither
     library's score targets citation correctness, so the custom metric
     earns its place rather than being redundant with the two libraries.
5. **Takeaway for later tasks**: don't trust a single RAGAS/TruLens score
   on a refusal answer at face value — these metrics need either a larger
   sample (multiple runs, averaged) or a special case for
   `answer == NOT_FOUND_MESSAGE` before they're used to gate anything.
   The citation-precision metric is the most directly interpretable of
   the three for this project's specific concern (does the model cite
   real pages), and `grade`'s observed non-determinism is now evidenced
   twice (tasks #14 and #16) — worth keeping in mind before relying on it
   as a hard gate in Phase 8+ without some form of averaging or
   retrying.
