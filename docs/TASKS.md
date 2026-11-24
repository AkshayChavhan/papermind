# Tasks

Every task we work on gets a row here. Status is updated the moment the task is actually done — not before.

| # | Task | Status | Learning doc(s) | Notes |
|---|------|--------|------------------|-------|
| 1 | Initialize git for papermind | Done | [learning/01_repo_setup/01_init_git.md](../learning/01_repo_setup/01_init_git.md) | Scoped repo inside `papermind/`, independent of the parent folder's repo |
| 2 | Add Claude Code working rules (git + branch rules) | Done | — | Branch `02_claude_code_rules`, merged via PR #1 |
| 3 | Phase 1 · Step 1 — project structure + Python env | Done | [learning/02_backend_setup/01_project_setup.md](../learning/02_backend_setup/01_project_setup.md) | Branch `03_project_setup`; chose `venv` over `conda`/`uv` |
| 4 | Phase 1 · Step 2 — PDF ingestion w/ LlamaIndex loaders + chunking | Todo | — | |
| 5 | Phase 2 — Vector store + RAG (Qdrant local, hybrid search, re-ranker) | Todo | — | |
| 6 | Phase 3 — LLM layer (LangChain wrappers, 4-provider config switch) | Todo | — | Paid APIs involved — will warn before use |
| 7 | Phase 4 — Prompts v1 → v2 → v3, compared on eval scores | Todo | — | |
| 8 | Phase 5 — LangGraph workflow (retrieve → grade → generate → verify → not-found) | Todo | — | |
| 9 | Phase 6 — FastAPI service + Flask ingestion service | Todo | — | |
| 10 | Phase 7 — Evaluation (RAGAS, TruLens, custom citation check) | Todo | — | |
| 11 | Phase 8 — Observability (LangSmith, JSON logs, notebook plots) | Todo | — | |
| 12 | Phase 9 — Streamlit demo | Todo | — | |
| 13 | Phase 10 — Next.js chat UI (streaming, citation links) | Todo | — | |
| 14 | Phase 11 — Deployment to VPS with PM2 | Todo | — | |

**Status values:** `Todo` · `In Progress` · `Done`

## How a row gets added

1. We agree on a task.
2. A row is added here with status `Todo`, and a matching learning doc is started under [`../learning/`](../learning/).
3. Status moves to `In Progress` while work happens.
4. When done, status moves to `Done`, the learning doc is rechecked/updated, and you're asked to confirm it makes sense.
