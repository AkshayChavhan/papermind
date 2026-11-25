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
                                        [naive: no citation instructions — v2/v3 next]
```

PDF ingestion + chunking, the Qdrant local-mode collection, embedding +
upserting the chunks, dense search, hybrid (dense + BM25, fused with RRF)
search, and a cross-encoder re-ranker on top of the hybrid candidates
complete Phase 2 end to end. Phase 3 adds a swappable LLM layer
(`backend/src/llm/providers.py`'s `get_llm()`), with OpenAI wired up and
tested and the other 3 providers stubbed for now. Phase 4 is building the
RAG answer prompt itself, v1 → v2 → v3; `backend/src/prompts/v1.py` is the
deliberately naive baseline, confirmed (via a real OpenAI call on real
retrieved chunks) to never cite pages
(`backend/notebooks/01_pdf_ingestion.ipynb`, `02_qdrant_setup.ipynb`,
`03_embed_upsert.ipynb`, `04_dense_search.ipynb`, `05_hybrid_search.ipynb`,
`06_reranker.ipynb`, `07_llm_provider_switch.ipynb`, `08_prompt_v1.ipynb`)
— see
[learning/03_documents_ingestion/01_pdf_ingestion_chunking.md](../learning/03_documents_ingestion/01_pdf_ingestion_chunking.md),
[learning/04_rag_pipeline/01_qdrant_setup.md](../learning/04_rag_pipeline/01_qdrant_setup.md),
[learning/04_rag_pipeline/02_embed_upsert.md](../learning/04_rag_pipeline/02_embed_upsert.md),
[learning/04_rag_pipeline/03_dense_search.md](../learning/04_rag_pipeline/03_dense_search.md),
[learning/04_rag_pipeline/04_hybrid_search.md](../learning/04_rag_pipeline/04_hybrid_search.md),
[learning/04_rag_pipeline/05_reranker.md](../learning/04_rag_pipeline/05_reranker.md),
[learning/05_llm_layer/01_langchain_provider_switch.md](../learning/05_llm_layer/01_langchain_provider_switch.md),
and
[learning/06_prompts/01_prompt_v1.md](../learning/06_prompts/01_prompt_v1.md).

(Updates as each phase in [TASKS.md](./TASKS.md) actually lands.)

## Related docs

- [TASKS.md](./TASKS.md) — what's being worked on, and what's done
- [PROJECT_FLOW.md](./PROJECT_FLOW.md) — how a task moves from idea to done, and (later) how data/requests move through the system
- [../learning/](../learning/) — step-by-step write-ups of *how* each piece was built and *why*
