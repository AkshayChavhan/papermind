# Architecture — papermind

> Status: **stack decided, pieces being built one at a time.** This doc fills in as each piece actually exists.

## What this project is

**papermind** is a learning project: a research-paper Q&A app. Upload PDFs,
ask questions, get answers with page-level citations and quality scores.
The goal isn't just "make it work" — it's to practice building it the way a
high-standards company would (clean structure, documented decisions,
reviewable steps) *and* to learn the Python/RAG/LLM stack along the way,
since the primary stack outside this is JS/TS (React, Next.js, Node).

## Stack (decided, built up phase by phase — see TASKS.md)

- **Backend core:** Python
- **LLM orchestration:** LangChain, LangGraph, LlamaIndex
- **Vector DB:** Qdrant (local mode, main build) — Pinecone/Weaviate/ChromaDB covered as comparisons
- **LLM APIs:** OpenAI, Anthropic, Google Vertex AI, AWS Bedrock (switchable via config)
- **RAG:** chunking, embeddings, hybrid search, re-ranking
- **API:** FastAPI (main), Flask (ingestion service)
- **Front-end:** Next.js (TypeScript), streaming chat UI with citation links
- **Evaluation:** RAGAS, TruLens, custom citation-check metric
- **Observability:** LangSmith, JSON logging, Jupyter notebooks
- **Demo:** Streamlit (before the Next.js UI)
- **Deployment:** VPS + PM2

## Pieces built so far

```
┌───────────┐     ┌───────────┐     ┌─────────────┐
│ PDF file  │ --> │ PDFReader │ --> │  Sentence   │
│           │     │ (pages w/ │     │  Splitter   │
│           │     │ page_label)│     │ (512/50)    │
└───────────┘     └───────────┘     └──────┬──────┘
                                             │
                         ┌───────────────────┴───────────────────┐
                         ▼                                       ▼
                  fastembed dense                        fastembed bm25
                   (384-dim)                                (sparse)
                         └───────────────────┬───────────────────┘
                                             ▼
                              ┌─────────────────────────────┐
                              │ Qdrant collection             │
                              │ papermind_chunks               │
                              │ (named vectors: dense + bm25)  │
                              └──────────────┬──────────────┘
                                              ▲
                  question --(same embedders)--> Prefetch(dense)+Prefetch(bm25)
                                              │
                                   FusionQuery(RRF) --> top-k (wide) candidates
                                              │
                                   TextCrossEncoder re-rank --> final top-k
                                              │
                                              ▼
                                    backend/src/llm/providers.py
                                        get_llm("openai") --> ChatOpenAI  [wired + tested]
                                        get_llm("anthropic"/"vertexai"/"bedrock") --> not wired yet
                                              │
                                              ▼
                                    backend/src/prompts/v1.py
                                        build_prompt(question, chunks) --> answer(..., llm)
                                        [naive: no citation instructions]
                                              │
                                              ▼
                                    backend/src/prompts/v2.py
                                        page-labeled chunks + cite-every-claim instruction
                                        [verified: correctly cites (page 1)/(page 4)]
                                              │
                                              ▼
                                    backend/src/prompts/v3.py
                                        + refuse-if-not-grounded instruction
                                        [compared v1/v2/v3 on grounded + ungrounded Qs]
                                              │
                                              ▼
                                    backend/src/graph/workflow.py
                                        build_graph(pipeline, llm):
                                        retrieve -> grade -(relevant?)-> generate -> verify
                                                      │                               │
                                                      └──(not)──> not_found <─(not grounded)┘
                                              │
                        ┌─────────────────────┴─────────────────────┐
                        ▼                                           ▼
            backend/src/services/ingestion_service.py   backend/src/services/api.py
                Flask: POST /ingest                       FastAPI: POST /ask
                [verified: real upload -> 4 chunks]        [verified: real ask -> cited answer]
                                              │
                                              ▼
                        backend/src/evaluation/citation_check.py
                            citation_precision(answer, chunks)
                            [+ RAGAS faithfulness, TruLens groundedness in notebook 13 —
                             both libraries disagree sharply on refusal answers; the
                             custom citation metric is the one that behaves as designed]
                                              │
                                              ▼
                        backend/src/observability/request_log.py
                            timed_invoke(graph, question) --> data/logs/requests.jsonl
                            [wired into POST /ask; LangSmith tracing verified live]
                                              │
                                              ▼
                        backend/streamlit_app.py (single process, own pipeline+graph)
                            [verified live in a real browser: upload -> ingest -> cited answer]
                                              │
                                              ▼
            backend: POST /ask/stream (SSE, src/graph/streaming.py)
                            │
                            ▼
            frontend/ (Next.js 16, App Router) — src/app/page.tsx
                chat page: fetch + ReadableStream reader, parses SSE itself
                citations rendered as styled (page N) badges
                [verified live: real backend + real `next dev`, real browser click-through]

  Deployment (docker-compose.yml + ecosystem.config.js):
    docker compose up -d qdrant (server mode, not local-mode)
            │
            ├──────────────┬─────────────────────┐
            ▼               ▼                     ▼
    pm2: papermind-api  pm2: papermind-ingestion  pm2: papermind-frontend
    (main_api.py)       (main_ingestion.py)        (next start)
    [verified for real: 2 separate live processes sharing 1 Qdrant server;
     PM2 start/health/restart all confirmed. Real VPS access: pending —
     see docs/DEPLOYMENT.md]
```

PDF ingestion + chunking, the Qdrant local-mode collection, embedding +
upserting the chunks, dense search, hybrid (dense + BM25, fused with RRF)
search, and a cross-encoder re-ranker on top of the hybrid candidates
complete Phase 2 end to end. Phase 3 adds a swappable LLM layer
(`backend/src/llm/providers.py`'s `get_llm()`), with OpenAI wired up and
tested and the other 3 providers stubbed for now. Phase 4 is building the
RAG answer prompt itself, v1 → v2 → v3; `backend/src/prompts/v1.py` is the
deliberately naive baseline, confirmed (via a real OpenAI call on real
retrieved chunks) to never cite pages, and `backend/src/prompts/v2.py` adds
page-labeled chunks + a cite-every-claim instruction, confirmed (same real
pipeline) to correctly cite the right page per claim.
`backend/src/prompts/v3.py` adds a refuse-if-not-grounded instruction;
comparing v1/v2/v3 on a grounded and an ungrounded question found
gpt-4o-mini already declines fully unrelated context even under v1, so
v3's real effect so far is a recall/strictness trade-off on partially
grounded questions rather than blocking outright hallucination — formal
RAGAS/TruLens evaluation (task #16) is needed to go beyond manual spot
checks. Phase 5 wires retrieval + `get_llm()` + prompt v3 into one
LangGraph workflow (`backend/src/graph/workflow.py`), with a `grade` gate
before generation and a `verify` gate after; retrieval logic itself moved
out of notebooks into `backend/src/retrieval/pipeline.py`'s
`RetrievalPipeline` so the graph can call it as code. Verified on a
grounded, an off-topic, and a topically-close-but-ungrounded question;
`grade` turned out to catch both negative cases before generation, so
`verify`'s citation check hasn't yet been exercised by a real failure —
a known gap for task #16 to close. Phase 6 exposes that graph over HTTP:
`backend/src/services/api.py` (FastAPI, `POST /ask`) and
`backend/src/services/ingestion_service.py` (Flask, `POST /ingest`),
verified with a real ingest → ask round trip. Local-mode Qdrant's file
lock means these two can't run as separate live processes yet — both
were tested in-process, sharing one `RetrievalPipeline`; moving to Qdrant
server mode for real concurrent processes is Phase 11's job. Phase 7 adds
formal evaluation: RAGAS faithfulness and TruLens groundedness (both
run in `13_evaluation.ipynb`) scored the same literal refusal answer
inconsistently depending on context, and TruLens stayed high regardless
of actual correctness — neither targets citation correctness directly,
which is why `backend/src/evaluation/citation_check.py`'s
`citation_precision()` exists as a code-only, deterministic third check,
and it's the one that behaved exactly as designed. Phase 8 adds JSON
request logging (`backend/src/observability/request_log.py`'s
`timed_invoke`, wired into `POST /ask`) and a notebook that plots logged
latency — refused answers measurably short-circuit `grade` 2–4x faster
than a full grounded answer. LangSmith tracing (documented in
`.env.example` since Phase 8) is now verified live: a real
`LANGCHAIN_API_KEY` was added to `backend/.env` and a real `ChatOpenAI`
run showed up in the `papermind` LangSmith project, with zero code
change in `get_llm()`/`build_graph()`.
Phase 9 adds `backend/streamlit_app.py`, a single-process demo (own
`RetrievalPipeline` + graph, sidestepping the Qdrant local-mode lock
rather than fighting it) verified end to end in a real browser: real PDF
upload, real ingest, a real cited answer, and a real refusal — the same
`grade` non-determinism from tasks #14/#16 surfaced a 4th time, live in
the UI. Phase 10 adds the real front-end: `backend/src/graph/streaming.py`
streams the `generate` step's tokens over a new `POST /ask/stream` SSE
endpoint (a parallel path alongside the unchanged, non-streaming
`POST /ask`), and `frontend/` (Next.js 16, TypeScript, App Router) is a
single chat page that reads that stream itself (no `EventSource`, since
it needs a POST body) and renders `(page N)` citations as styled badges.
`backend/run_api.py` is a new real entrypoint for running the FastAPI
service standalone. Verified with real, separately-running backend and
frontend dev servers driven from an actual browser — this is also where
a real CORS port mismatch was caught (port 3000 was already taken by an
unrelated process on this machine, so the backend's CORS had to accept
any localhost port, not one fixed origin). Phase 11 closes the last
deferred item from tasks #15/#17/#18: `RetrievalPipeline` now supports
Qdrant **server mode** (`url=`) alongside local-mode, and the fix was
proven for real — a real `docker compose up` Qdrant server, two real
separate processes (query + ingestion) running at the same time,
ingesting through one and querying through the other successfully, all
managed by a real local PM2 instance (`ecosystem.config.js`). The one
remaining piece is a real VPS to deploy onto — pending, no SSH/VPS access
in this environment; see [`docs/DEPLOYMENT.md`](./DEPLOYMENT.md)
(`backend/notebooks/01_pdf_ingestion.ipynb`, `02_qdrant_setup.ipynb`,
`03_embed_upsert.ipynb`, `04_dense_search.ipynb`, `05_hybrid_search.ipynb`,
`06_reranker.ipynb`, `07_llm_provider_switch.ipynb`, `08_prompt_v1.ipynb`,
`09_prompt_v2.ipynb`, `10_prompt_v3.ipynb`, `11_langgraph_workflow.ipynb`,
`12_api_services.ipynb`, `13_evaluation.ipynb`, `14_observability.ipynb`)
— see
[learning/03_documents_ingestion/01_pdf_ingestion_chunking.md](../learning/03_documents_ingestion/01_pdf_ingestion_chunking.md),
[learning/04_rag_pipeline/01_qdrant_setup.md](../learning/04_rag_pipeline/01_qdrant_setup.md),
[learning/04_rag_pipeline/02_embed_upsert.md](../learning/04_rag_pipeline/02_embed_upsert.md),
[learning/04_rag_pipeline/03_dense_search.md](../learning/04_rag_pipeline/03_dense_search.md),
[learning/04_rag_pipeline/04_hybrid_search.md](../learning/04_rag_pipeline/04_hybrid_search.md),
[learning/04_rag_pipeline/05_reranker.md](../learning/04_rag_pipeline/05_reranker.md),
[learning/05_llm_layer/01_langchain_provider_switch.md](../learning/05_llm_layer/01_langchain_provider_switch.md),
[learning/06_prompts/01_prompt_v1.md](../learning/06_prompts/01_prompt_v1.md),
[learning/06_prompts/02_prompt_v2.md](../learning/06_prompts/02_prompt_v2.md),
[learning/06_prompts/03_prompt_v3.md](../learning/06_prompts/03_prompt_v3.md),
[learning/07_langgraph/01_langgraph_workflow.md](../learning/07_langgraph/01_langgraph_workflow.md),
[learning/08_api_services/01_fastapi_flask_services.md](../learning/08_api_services/01_fastapi_flask_services.md),
[learning/09_evaluation/01_ragas_trulens_citation_check.md](../learning/09_evaluation/01_ragas_trulens_citation_check.md),
[learning/10_observability/01_json_logging_and_plots.md](../learning/10_observability/01_json_logging_and_plots.md),
[learning/11_streamlit_demo/01_streamlit_demo.md](../learning/11_streamlit_demo/01_streamlit_demo.md),
[learning/12_nextjs_chat_ui/01_streaming_chat_citation_links.md](../learning/12_nextjs_chat_ui/01_streaming_chat_citation_links.md),
and
[learning/13_deployment/01_vps_pm2_deployment.md](../learning/13_deployment/01_vps_pm2_deployment.md).

(Updates as each phase in [TASKS.md](./TASKS.md) actually lands.)

## Related docs

- [TASKS.md](./TASKS.md) — what's being worked on, and what's done
- [PROJECT_FLOW.md](./PROJECT_FLOW.md) — how a task moves from idea to done, and (later) how data/requests move through the system
- [DEPLOYMENT.md](./DEPLOYMENT.md) — what's verified locally vs. pending a real VPS
- [../learning/](../learning/) — step-by-step write-ups of *how* each piece was built and *why*
