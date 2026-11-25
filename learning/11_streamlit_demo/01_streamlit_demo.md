# 01 — Phase 9: Streamlit demo

## What's about to happen

Every piece has now been used from code (notebooks) or HTTP
(`curl`/test clients, task #15) — never from something a non-technical
person could actually click through. Phase 9 adds a single-page
Streamlit app: upload a PDF, ask a question, see the answer with its
retrieved pages and whether it was grounded.

## Why this way

**One process, not three — and that's a direct consequence of task
#15's documented constraint**
The FastAPI/Flask services from Phase 6 can't both stay open against the
same local-mode Qdrant storage at once (file lock — see
`learning/08_api_services`). Rather than fight that constraint for a
demo, this Streamlit app owns its own `RetrievalPipeline` and graph
directly, in-process — exactly the "single process" case that constraint
already allows. It does **not** call the FastAPI `/ask` or Flask
`/ingest` endpoints over HTTP; those remain Phase 6's deliverable for a
real multi-process deployment (Phase 11, once Qdrant moves to server
mode).

**`st.cache_resource`, not re-building the pipeline per interaction**
Streamlit re-runs the whole script top-to-bottom on every UI interaction
(typing a question, clicking a button). Without caching, that would
re-load the embedding/rerank models and reopen the Qdrant client every
keystroke. `st.cache_resource` keeps one `RetrievalPipeline` and one
compiled graph alive across reruns within a session — the same reason
task #14's `build_graph(pipeline, llm)` takes them as arguments instead
of constructing them internally.

**Logs to the same `request_log` module as the FastAPI service**
Reuses `timed_invoke` from task #17 instead of a separate ad-hoc
print/log statement, so every real question asked through this demo
shows up the same way a real `/ask` call would, in the same JSON format.

**Verification: headless health check + a real browser click-through**
A Streamlit app can't be "executed" top-to-bottom the way a notebook can
— it's a long-running UI server. Verification here has two layers: a
headless check that the server actually boots (`streamlit run` +
`/_stcore/health` returns `ok`, proving no import/syntax error), and then
an actual browser session driving the real upload → ingest → ask flow,
since this project's own standard (see CLAUDE.md) is to use a UI change
in a real browser before calling it done, not just trust that the code
looks right.

## Diagram

```
  streamlit run backend/streamlit_app.py
            │
            ▼
  st.cache_resource: one RetrievalPipeline + one compiled graph
            │
   ┌────────┴────────┐
   ▼                 ▼
 file_uploader   text_input (question)
   │                 │
   ▼                 ▼
 pipeline.ingest()  timed_invoke(graph, question)  ──> answer, pages,
   (PDF -> chunks)                                     grounded, logged
```

## What we did

1. Added `backend/streamlit_app.py`: upload + ingest, then an input box
   that calls `timed_invoke(graph, question)` and shows the answer,
   `grounded` flag, and an expander with the real retrieved pages.
2. Started the server for real (`streamlit run streamlit_app.py
   --server.headless true`) and confirmed `/_stcore/health` returned
   `ok` — the app imports and boots cleanly.
3. **Drove the actual UI in a real browser** (not just the headless
   check): uploaded a real generated `sample.pdf`, clicked "Ingest PDF",
   asked two real questions, and read the real rendered output.
4. Results — fully real, including one more instance of the same
   non-determinism documented in tasks #14/#16:
   - **"How is citation accuracy measured in this paper?"** — `Ingested 4
     chunks from sample.pdf` appeared first, confirming the upload →
     `pipeline.ingest()` path works through the actual file uploader
     widget, not just in a notebook. The question itself was graded
     **not relevant** this run and showed the refusal message with
     `Grounded: False` — the *same* question that's flipped between
     relevant/not-relevant across tasks #11/#14/#16's different runs,
     now observed a 4th time, in the real UI this time, not just a
     notebook. The "Retrieved pages" expander still showed the real
     page 1/page 4 text underneath, confirming retrieval ran even though
     generation was skipped.
   - **"How are documents split into chunks?"** — graded relevant,
     generated a real answer citing `(page 3)` twice, correctly, with
     `Grounded: True`, and the expander showed the real page 3 (Method)
     and page 2 (Introduction) content.
5. Not tested: multiple concurrent users/sessions, or uploading a second,
   different PDF to replace the first (the cached pipeline/graph persist
   across reruns within one `streamlit run` process, consistent with the
   caching design, but a second real document wasn't tried here).
