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
┌───────────┐     ┌───────────┐     ┌─────────────┐     ┌─────────────┐
│ PDF file  │ --> │ PDFReader │ --> │  Sentence   │ --> │  fastembed   │
│           │     │ (pages w/ │     │  Splitter   │     │  (384-dim)   │
│           │     │ page_label)│     │ (512/50)    │     │      │      │
└───────────┘     └───────────┘     └─────────────┘     └──────┼──────┘
                                                                 ▼
                                                   ┌─────────────────────┐
                                                   │ Qdrant collection    │
                                                   │ papermind_chunks     │
                                                   │ (populated)          │
                                                   └──────────┬──────────┘
                                                                ▲
                            question --(fastembed)--> query vector
                                                                │
                                                     query_points (top-k)
```

PDF ingestion + chunking, the Qdrant local-mode collection, embedding +
upserting the chunks, and dense vector search over them are the pieces
built so far (`backend/notebooks/01_pdf_ingestion.ipynb`,
`02_qdrant_setup.ipynb`, `03_embed_upsert.ipynb`, `04_dense_search.ipynb`)
— see
[learning/03_documents_ingestion/01_pdf_ingestion_chunking.md](../learning/03_documents_ingestion/01_pdf_ingestion_chunking.md),
[learning/04_rag_pipeline/01_qdrant_setup.md](../learning/04_rag_pipeline/01_qdrant_setup.md),
[learning/04_rag_pipeline/02_embed_upsert.md](../learning/04_rag_pipeline/02_embed_upsert.md),
and
[learning/04_rag_pipeline/03_dense_search.md](../learning/04_rag_pipeline/03_dense_search.md).

(Updates as each phase in [TASKS.md](./TASKS.md) actually lands.)

## Related docs

- [TASKS.md](./TASKS.md) — what's being worked on, and what's done
- [PROJECT_FLOW.md](./PROJECT_FLOW.md) — how a task moves from idea to done, and (later) how data/requests move through the system
- [../learning/](../learning/) — step-by-step write-ups of *how* each piece was built and *why*
