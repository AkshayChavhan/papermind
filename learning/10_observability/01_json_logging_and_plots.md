# 01 — Phase 8: Observability (JSON logging + notebook plots + LangSmith tracing)

## What's about to happen

Every number produced so far (tasks #13/#14/#16's scores and verdicts) was
read once, by hand, straight out of a notebook cell's printed output.
Phase 8 makes that durable and visual instead of disposable:

1. **JSON request logging** — every `graph.invoke(...)` call gets wrapped
   so it appends one structured JSON line (question, retrieved pages,
   `grounded`, answer length, duration) to `data/logs/requests.jsonl`.
   Wired into the FastAPI `/ask` route from task #15, so every real
   request through the service gets logged automatically, not just
   notebook runs.
2. **Notebook plots** — a small notebook replays several questions through
   the logger, then reads the log file back and plots latency and the
   grounded/refused split with `matplotlib`.
3. **LangSmith tracing — now verified with a real key.** The stack
   decision calls for LangSmith tracing. Initially there was no
   `LANGCHAIN_API_KEY` in `.env`, so this task added the `.env.example`
   entries and documented what flipping them on would do. The user has
   since created a LangSmith account and added a real key to `backend/.env`
   — this update confirms the prediction was correct: LangChain and
   LangGraph auto-instrument purely from environment variables, with zero
   code change in `get_llm()` or `build_graph()`.

## Why this way

**JSON logging first, because it needs nothing external**
Unlike LangSmith, structured logging to a local file has no account, no
quota, no cost — it's the part of "observability" buildable right now
with what's already in `.env`. Blocking the whole task on a credential
that isn't ready yet, rather than building what's independently useful
and flagging the rest as pending, would waste the parts that don't need
to wait.

**One small wrapper function, not a logging node added to the graph**
`timed_invoke(graph, question)` wraps `graph.invoke` from the outside
(timing + logging), rather than adding a "log" node inside the LangGraph
`StateGraph` itself. The graph's job is still just
retrieve→grade→generate→verify→not_found; logging is a cross-cutting
concern about *calling* the graph, not a step *in* the answer pipeline,
so it stays outside it — the same reasoning that kept `verify` as a cheap
code check instead of folding evaluation logic into the graph in task
#14.

**LangSmith is genuinely zero extra code, which is worth proving, not
just asserting**
LangChain's tracing is activated purely by `LANGCHAIN_TRACING_V2=true` +
`LANGCHAIN_API_KEY` in the environment — nothing in `get_llm()` or
`build_graph()` needs to change. This task adds those two lines (commented
out, like the other not-yet-wired providers in `.env.example` since task
#10) and says plainly in this doc that it's untested without a real key,
rather than quietly skipping the stack's observability decision without
explanation.

## Diagram

```
  POST /ask ──> timed_invoke(graph, question)
                     │
                     ├──> graph.invoke(...)  (Phase 5, unchanged)
                     │
                     └──> log_request(...) ──> data/logs/requests.jsonl
                                                 {"timestamp", "question",
                                                  "pages", "grounded",
                                                  "answer_length",
                                                  "duration_s"}
                                                       │
                                                       ▼
                                        notebook 14: read log, plot
                                        latency + grounded/refused split

  LangSmith tracing: LANGCHAIN_TRACING_V2=true + LANGCHAIN_API_KEY in .env
  (real key set — verified; see "What we did")
```

## What we did

1. Added `backend/src/observability/request_log.py`: `log_request(...)`
   appends one JSON line per call; `timed_invoke(graph, question)` times
   `graph.invoke` and logs it.
2. Wired `timed_invoke` into `backend/src/services/api.py`'s `POST /ask`
   route, replacing the direct `graph.invoke(...)` call — every real
   request through the FastAPI service now gets logged automatically.
3. Added `.env.example` entries for `LANGCHAIN_TRACING_V2`,
   `LANGCHAIN_API_KEY`, `LANGCHAIN_PROJECT` (commented out, matching the
   pattern used for the other not-yet-wired providers since task #10).
4. Added `backend/notebooks/14_observability.ipynb`: ran 5 real questions
   through `timed_invoke`, read the JSON log file back fresh (not from
   memory), and plotted per-question latency (colored by `grounded`) plus
   a grounded/refused count.
5. Result — the log is real and round-trips correctly, and it surfaced a
   genuinely useful pattern that wasn't obvious from reading printed
   answers alone:
   - **Grounded answers (full retrieve→grade→generate→verify path) took
     1.8–3.1s.** **Refused answers (short-circuited at `grade`) took only
     0.7–0.9s** — roughly 2–4x faster, because they skip the `generate`
     and `verify` LLM calls entirely. This is the two-gate design from
     task #14 paying off measurably, not just architecturally: a bad
     question costs noticeably less than a good one, which matters once
     real users can send arbitrary questions.
   - 5 rows logged, 5 rows read back, `duration_s` and `grounded` matched
     what each question's live run printed — confirms `timed_invoke`
     isn't silently dropping or miscounting requests.
6. **LangSmith — verified for real (2026-11-25).** The user created a
   LangSmith account and added a real `LANGCHAIN_API_KEY` +
   `LANGCHAIN_PROJECT=papermind` to `backend/.env`. Confirmed end-to-end,
   not just "the env vars are set":
   - Ran `get_llm("openai").invoke("Say OK")` with the real key loaded —
     no code change needed in `get_llm()` or `build_graph()`, exactly as
     predicted.
   - Queried the LangSmith REST API (`GET /sessions`) and found the
     `papermind` project already exists.
   - Queried `POST /runs/query` for that project and got back a real
     logged run: `ChatOpenAI`, `run_type: llm`, timestamped at the moment
     the call above was made.
   This closes the one item this task had left pending — tracing is live,
   not just wired.
