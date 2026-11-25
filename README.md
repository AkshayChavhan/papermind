# papermind

A personal learning project: a PDF research-paper Q&A RAG app, built
phase by phase as a vehicle for learning how to build to a high
engineering standard — the documentation trail matters as much as the
code. See [`CLAUDE.md`](CLAUDE.md) for the working rules this repo
follows.

## Docs

- [`docs/TASKS.md`](docs/TASKS.md) — every task, its status, and the
  learning doc behind it.
- [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) — the pieces built so
  far and how they fit together.
- [`docs/PROJECT_FLOW.md`](docs/PROJECT_FLOW.md) — how data moves
  through the system.
- [`docs/DEPLOYMENT.md`](docs/DEPLOYMENT.md) — what's verified vs.
  pending for deployment.
- [`learning/`](learning/) — one numbered folder per topic, explaining
  what happened and why, in the order topics were introduced.

## Pending

Everything in `docs/TASKS.md` is `Done`. One item remains blocked on
something only a real server can provide:

- **Real VPS deployment** — Qdrant server mode, `docker-compose.yml`,
  the PM2 `ecosystem.config.js`, and the production entrypoints are all
  written and verified locally (including the multi-process concurrency
  fix, proven with two live processes sharing one Qdrant server). The
  actual "provision a server and run this" step needs real SSH/VPS
  access, which doesn't exist in this environment. See
  [`docs/DEPLOYMENT.md`](docs/DEPLOYMENT.md) for the exact remaining
  steps.

LangSmith tracing was the other originally-pending item; it's since been
verified working end to end with a real API key (see
[`learning/10_observability/01_json_logging_and_plots.md`](learning/10_observability/01_json_logging_and_plots.md)).
