# 01 — Phase 10: Next.js streaming chat UI with citation links

## What's about to happen

Phase 9 gave a clickable demo, but Streamlit is explicitly "before the
Next.js UI" in the stack decision — this is the real front-end, in the
stack the user actually works in day to day (React/Next.js/TypeScript),
unlike the rest of this project which has been deliberately new territory
(Python/RAG). Two things from the stack decision need a real answer here:

1. **Streaming** — so far every answer (notebooks, FastAPI, Streamlit) is
   a single blocking call: ask, wait several seconds, get the whole
   answer at once. A chat UI should show tokens arriving live.
2. **Citation links** — `(page N)` citations have existed as plain text
   since task #12 (prompt v2). This task renders them as visually
   distinct inline markers in the chat UI.

## Why this way

**A new streaming endpoint, not a streaming rewrite of the LangGraph
workflow**
The existing `POST /ask` (task #15) calls `graph.invoke(...)`, which runs
the whole `retrieve → grade → generate → verify → not_found` graph
synchronously and returns one final `GraphState`. Making *that* stream
token-by-token would mean restructuring every node into an async
generator — a much bigger change than this task needs, and it would
touch Phase 5's already-verified workflow. Instead, `POST /ask/stream`
is a parallel, additive endpoint: it re-implements just enough of the
same retrieve → grade → generate logic to stream the `generate` step's
tokens live via Server-Sent Events, while reusing the same prompt (v3),
pipeline, and citation logic. `POST /ask` (non-streaming) stays exactly
as it was for the Flask/Streamlit/notebook callers that already use it.

**Server-Sent Events over `fetch`, not a WebSocket**
This is one-directional (server → client token stream) with no need for
the client to send more than the initial question, so SSE is the simpler
primitive. The browser's built-in `EventSource` can't send a POST body
(it's GET-only), so the Next.js client reads the stream manually via the
Fetch Streams API (`response.body.getReader()`), parsing `data: {...}\n\n`
lines itself — a well-known, standard pattern for POST-based SSE.

**Citation markers are styled text, not real deep-links into a PDF
viewer**
There's no PDF viewer in this UI (that's out of scope here) — "citation
links" is implemented honestly as what's actually buildable right now:
the client regex-matches `(page N)` in the streamed answer text and
renders it as a distinct styled inline badge, making citations visually
scannable. Calling this a deep-link to an actual page location would be
overclaiming; it's recorded here as a possible follow-up, not done.

**Minimal Next.js app, App Router, one page**
No routing, no auth, no multi-conversation history — this is a single
chat page matching the current single-question backend, mirroring the
same "build exactly what's needed" discipline used for every prior
phase's scope (e.g. task #18's single-page Streamlit demo).

## Diagram

```
  Next.js page (frontend/app/page.tsx)
       │  fetch POST /ask/stream {"question": "..."}
       ▼
  FastAPI POST /ask/stream (backend/src/services/api.py)
       │
       ├── pipeline.retrieve(question)              (Phase 2, unchanged)
       ├── grade (1 LLM call, non-streamed, reused prompt from Phase 5)
       │        not relevant? ──> SSE: one "done" event, not_found message
       ▼ relevant
       llm.stream(prompt_v3)  ──> SSE: one "token" event per chunk
       │
       verify (citation-presence check, same as Phase 5)
       ▼
       SSE: final "done" event — grounded, pages, full answer

  Client: appends each "token" event to the visible answer as it arrives;
  on "done", renders citation badges by regex-matching (page N) in the
  final text.
```

## What we did

1. Added `backend/src/graph/streaming.py`'s `stream_answer(pipeline, llm,
   question)`: a generator reusing the Phase 5 `grade` prompt and the
   Phase 4 v3 prompt, yielding `{"type": "token", ...}` events while
   `llm.stream(prompt)` produces the answer, then one final
   `{"type": "done", "answer", "grounded", "pages"}` event.
2. Added `POST /ask/stream` to `backend/src/services/api.py` (Server-Sent
   Events via `StreamingResponse`), plus CORS middleware
   (`allow_origin_regex=r"http://localhost:\d+"` — see below for why a
   fixed port didn't work) so a browser app on a different origin/port
   can call it.
3. Added `backend/run_api.py`: a real entrypoint to run the FastAPI
   service standalone (ingests the sample PDF, then `uvicorn.run(...)`)
   — this didn't exist before; every prior FastAPI test used an in-process
   `TestClient`, never a real running server a browser could hit.
4. Scaffolded `frontend/` with `create-next-app` (TypeScript, App Router).
   First attempt pinned Next 14.2.33, which `npm install` itself flagged
   as having a known security vulnerability — rescaffolded with the
   latest stable release (16.4.6) instead, which installed with 0
   reported vulnerabilities.
5. Built `frontend/src/app/page.tsx`: a single chat page that `fetch`es
   `/ask/stream`, reads the response body with the Fetch Streams API
   (`response.body.getReader()`), parses `data: {...}\n\n` SSE frames
   itself (the browser's built-in `EventSource` can't send a POST body),
   and appends each token to the in-progress message as it arrives.
   Citations are rendered by regex-matching `(page N)` in the final text
   and wrapping matches in a styled `<span class="citation">` badge —
   a visual marker, not a deep-link into a PDF viewer (none exists in
   this UI).
6. **Real verification, not just code review**: ran `next build` (passed,
   0 TypeScript/lint errors), then started the real FastAPI server
   (`run_api.py`) and the real Next.js dev server, and drove the actual
   page in a browser.
   - Hit a real environment snag: port 3000 was already occupied by an
     unrelated local dev server (someone else's portfolio site running
     on this machine), so Next.js auto-moved to port 3001. The backend's
     CORS was initially pinned to `http://localhost:3000`, which would
     have silently blocked the real frontend — caught by actually
     loading the page in a browser (it showed the wrong site at :3000
     until the mismatch was noticed), not by code review. Fixed by
     switching CORS to a `localhost:<any port>` regex instead of a fixed
     origin, since the exact dev port isn't something this app should
     assume.
   - Asked two real grounded questions through the real browser UI:
     "How are documents split into chunks?" → answer correctly rendered
     with two `(page 3)` citation badges, `grounded · pages: 3, 2`.
     "What does the abstract say this paper studies?" → answer correctly
     rendered with a `(page 1)` citation badge, `grounded · pages: 1, 4`.
   - Confirmed token-level streaming directly at the backend first (a
     `TestClient` streaming request showed ~50 separate `token` SSE
     events arriving one word/sub-word at a time before the final `done`
     event) — this is the strongest evidence the streaming is real, since
     gpt-4o-mini answers fast enough on this short a context that a
     browser screenshot couldn't reliably catch a visibly half-typed
     sentence mid-render.
7. Not tested: a question that gets refused through the streaming path
   (the "not relevant" `grade` branch), multiple simultaneous chat
   sessions, or a second/different PDF upload through this UI (there's no
   upload control on this page — it assumes a document was already
   ingested, e.g. via Phase 9's Streamlit app or `run_api.py`'s own
   ingest-on-startup).
