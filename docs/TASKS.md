# Tasks

Every task we work on gets a row here. Status is updated the moment the task is actually done — not before.

| # | Task | Status | Learning doc(s) | Notes |
|---|------|--------|------------------|-------|
| 1 | Initialize git for papermind | Done | [learning/01_repo_setup/01_init_git.md](../learning/01_repo_setup/01_init_git.md) | Scoped repo inside `papermind/`, independent of the parent folder's repo |
| 2 | Add Claude Code working rules (git + branch rules) | Done | — | Branch `02_claude_code_rules`, merged via PR #1 |
| 3 | Phase 1 · Step 1 — project structure + Python env | Done | [learning/02_backend_setup/01_project_setup.md](../learning/02_backend_setup/01_project_setup.md) | Branch `03_project_setup`; chose `venv` over `conda`/`uv` |
| 4 | Phase 1 · Step 2 — PDF ingestion w/ LlamaIndex loaders + chunking | Done | [learning/03_documents_ingestion/01_pdf_ingestion_chunking.md](../learning/03_documents_ingestion/01_pdf_ingestion_chunking.md) | Branch `04_pdf_ingestion`; `PDFReader` + `SentenceSplitter` (512/50), page_label kept through chunking |
| 5 | Phase 2 · Step 1 — Qdrant running locally + collection created | Done | [learning/04_rag_pipeline/01_qdrant_setup.md](../learning/04_rag_pipeline/01_qdrant_setup.md) | Branch `05_qdrant_setup`; local mode (no Docker), `BAAI/bge-small-en-v1.5` (384-dim) via `fastembed` |
| 6 | Phase 2 · Step 2 — Embed chunks, upsert into Qdrant | Done | [learning/04_rag_pipeline/02_embed_upsert.md](../learning/04_rag_pipeline/02_embed_upsert.md) | Branch `06_embed_upsert`; `fastembed` vectors, uuid5 point IDs (idempotent re-runs), payload has `text`/`page_label`/`file_name`/`chunk_index` |
| 7 | Phase 2 · Step 3 — Dense vector search / retrieval (top-k + citations) | Done | [learning/04_rag_pipeline/03_dense_search.md](../learning/04_rag_pipeline/03_dense_search.md) | Branch `07_dense_search`; `query_points` API, verified top result matches the right page |
| 8 | Phase 2 · Step 4 — Hybrid search (dense + keyword/sparse) | Done | [learning/04_rag_pipeline/04_hybrid_search.md](../learning/04_rag_pipeline/04_hybrid_search.md) | Branch `08_hybrid_search`; named `dense`+`bm25` vectors, `fastembed` BM25, RRF fusion via `Prefetch`+`FusionQuery` |
| 9 | Phase 2 · Step 5 — Re-ranker on top of hybrid results | Done | [learning/04_rag_pipeline/05_reranker.md](../learning/04_rag_pipeline/05_reranker.md) | Branch `09_reranker`; `fastembed` `TextCrossEncoder` (`Xenova/ms-marco-MiniLM-L-6-v2`), over-fetch top 4 from hybrid search then re-rank down to top 2 |
| 10 | Phase 3 · Step 1 — LangChain LLM wrapper + 4-provider config switch | Done | [learning/05_llm_layer/01_langchain_provider_switch.md](../learning/05_llm_layer/01_langchain_provider_switch.md) | Branch `10_llm_layer`; `get_llm()` factory, OpenAI wired + verified with a real call, Anthropic/Vertex AI/Bedrock stubbed with `NotImplementedError` |
| 11 | Phase 4 · Step 1 — Prompt v1 (baseline RAG prompt: question + chunks → answer) | Done | [learning/06_prompts/01_prompt_v1.md](../learning/06_prompts/01_prompt_v1.md) | Branch `11_prompt_v1`; `backend/src/prompts/v1.py`; confirmed naive prompt never cites pages even though `page_label` is available |
| 12 | Phase 4 · Step 2 — Prompt v2 (add citation/grounding instructions) | Done | [learning/06_prompts/02_prompt_v2.md](../learning/06_prompts/02_prompt_v2.md) | Branch `12_prompt_v2`; `backend/src/prompts/v2.py`; page-labeled chunks + cite-every-claim instruction; verified v2 correctly cites (page 1)/(page 4) where v1 cited nothing |
| 13 | Phase 4 · Step 3 — Prompt v3 (refuse-if-not-grounded) + compare v1/v2/v3 | Done | [learning/06_prompts/03_prompt_v3.md](../learning/06_prompts/03_prompt_v3.md) | Branch `13_prompt_v3`; `backend/src/prompts/v3.py`; manual comparison found gpt-4o-mini already refuses fully unrelated context even with v1 — v3's refusal rule showed a recall/strictness trade-off instead; formal RAGAS/TruLens scoring remains task #16 |
| 14 | Phase 5 — LangGraph workflow (retrieve → grade → generate → verify → not-found) | Todo | — | |
| 15 | Phase 6 — FastAPI service + Flask ingestion service | Todo | — | |
| 16 | Phase 7 — Evaluation (RAGAS, TruLens, custom citation check) | Todo | — | |
| 17 | Phase 8 — Observability (LangSmith, JSON logs, notebook plots) | Todo | — | |
| 18 | Phase 9 — Streamlit demo | Todo | — | |
| 19 | Phase 10 — Next.js chat UI (streaming, citation links) | Todo | — | |
| 20 | Phase 11 — Deployment to VPS with PM2 | Todo | — | |

**Status values:** `Todo` · `In Progress` · `Done`

## How a row gets added

1. We agree on a task.
2. A row is added here with status `Todo`, and a matching learning doc is started under [`../learning/`](../learning/).
3. Status moves to `In Progress` while work happens.
4. When done, status moves to `Done`, the learning doc is rechecked/updated, and you're asked to confirm it makes sense.
