# 03 — Prompt v3 (refuse-if-not-grounded) + v1/v2/v3 comparison

## What's about to happen

v2 confirmed citations work when the context actually contains the answer.
It doesn't yet test the opposite case: what happens when the context
*doesn't* contain the answer? A prompt with no refusal rule will usually
still produce a plausible-sounding prose answer anyway — a hallucination
risk. v3 adds one more instruction on top of v2: if the context doesn't
contain enough information to answer, say so explicitly instead of
guessing. Then all three versions (v1, v2, v3) get run side by side on
**two** questions:

1. The same grounded question used in notebooks 08/09 (context does
   contain relevant info) — checks v3 didn't break what v2 already fixed.
2. A new question the retrieved chunks do *not* cover — checks whether v3
   actually refuses where v1/v2 would likely have guessed.

## Why this way

**Testing the failure mode directly, not just hoping the instruction works**
Earlier versions were tested with a question the context partially
covers. That's the wrong test for a refusal rule — of course nothing
refuses when there's *something* to talk about. v3 needs an ungrounded
question run through the same pipeline to actually observe refuse vs.
hallucinate.

**v3 keeps v2's citation rule and adds one more sentence**
v3 isn't a rewrite — it's v2's template plus one additional instruction
("If the context does not contain enough information to answer the
question, say so explicitly instead of guessing"). Isolating the one new
rule keeps this comparable to v2, same as v2 was to v1.

**Manual comparison, not RAGAS, for now**
As agreed before splitting this task: formal RAGAS/TruLens scoring is a
separate task (#16) once Phase 7 exists. For now the comparison is reading
three answers side by side and noting, honestly, which ones cite correctly
and which ones refuse appropriately.

## Diagram

```
 grounded question ──┐         ungrounded question ──┐
                     ▼                                ▼
         Phase 2 pipeline (hybrid search + re-rank, same as before)
                     │                                │
                     ▼                                ▼
          same top-k chunks as            top-k chunks that do NOT
          notebooks 08/09                  cover the question
                     │                                │
                     ▼                                ▼
      v1.answer / v2.answer / v3.answer  run on BOTH questions
                     │
                     ▼
      notebook prints all 6 answers side by side; learning doc records,
      honestly, which versions cite correctly and which refuse correctly
```

## What we did

1. Added `backend/src/prompts/v3.py`: same as v2 plus one more sentence —
   "If the context does not contain enough information to answer the
   question, say so explicitly instead of guessing."
2. Added `backend/notebooks/10_prompt_v3.ipynb`: retrieves chunks for two
   questions (the usual grounded one, plus a new ungrounded one — "What
   funding source supported this research?", which neither page covers),
   then runs all of v1/v2/v3 on both — 6 real OpenAI calls.
3. Result — more nuanced than expected, and worth recording honestly rather
   than forcing it to match the hypothesis:
   - **Grounded question**: all three versions hedged this run, not just
     v1. The question ("how is citation accuracy *measured*") was never
     fully answerable even from the real context — the paper only implies
     a method, it doesn't state one — so v1/v2/v3 all said some version of
     "the context doesn't specify the exact method." v2 cited `(page 1)`
     for the one claim it did make, but — unlike the notebook 09 run —
     didn't also cite page 4 this time; gpt-4o-mini's answers aren't
     perfectly deterministic run to run, which is itself worth knowing
     before trusting a single manual spot-check over automated eval (task
     #16). v3 gave the most terse answer, refusing fully rather than
     surfacing the partial, correctly-cited information v2 did — i.e. the
     refusal instruction can trade recall for strictness, not just block
     hallucination.
   - **Ungrounded question**: all three versions — including v1, which has
     no refusal instruction at all — correctly declined to invent a
     funding source. This disproves the simple version of the hypothesis:
     gpt-4o-mini already avoids confidently answering from *completely*
     unrelated context, with or without being told to. v3's refusal rule
     didn't need to do any work here because the baseline model was never
     going to guess on a topic this disconnected from the passages.
4. **Takeaway**: v3's refusal instruction is not proven harmful or
   pointless by this test, but this particular test case was too easy
   (totally unrelated context) to show it adding value over v1/v2, and
   the grounded case hints it may cost some recall on partially-covered
   questions. A harder test — context that's *topically* related but
   still missing the specific fact asked — is a better candidate for
   formal evaluation in task #16, where multiple runs and a real metric
   (not one manual read) can separate real signal from this kind of
   run-to-run noise.
