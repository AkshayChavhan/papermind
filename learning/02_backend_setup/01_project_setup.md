# 01 — Backend project structure + Python environment

## What's about to happen

This is Phase 1 · Step 1 of papermind. Before writing any ingestion code, we
need:
1. A `backend/` folder to hold all the Python code, separate from the docs/
   learning files already in the repo root.
2. An isolated Python environment, so papermind's packages (LangChain,
   LlamaIndex, FastAPI, etc.) don't pollute or depend on anything else
   installed system-wide.
3. A notebook folder for Phase 1's experiment (loading a PDF, chunking it).

## Why this way

**Isolation tool: venv vs conda vs uv**

| Option | What it is | Pros | Cons | Fits papermind? |
|---|---|---|---|---|
| `venv` (Python stdlib) | Built into Python 3, creates an isolated folder with its own `pip` | Zero install — already on this Mac; the standard every Python tutorial assumes; nothing new to learn | Slower installs than modern tools; no built-in lockfile (`pip freeze` is the manual version) | Yes — simplest path, nothing to install first |
| `conda` | A full package *and* environment manager, originally built for data science (handles compiled/binary deps like CUDA, MKL) | Great when you need non-Python binaries pip can't build | Heavy install (~500MB+), separate package index from PyPI, slower | No — not installed on this Mac, and nothing in our stack (LangChain/FastAPI/Qdrant client) needs conda's binary-package powers |
| `uv` | A modern, Rust-based replacement for pip + venv (by Astral) | 10–100x faster installs, built-in lockfile (`uv.lock`), can even install Python versions for you | Needs `brew install uv` first (not installed on this Mac yet) — one more tool to learn on top of Python itself | Good *upgrade* later, not needed to start |

**Decision: `venv`.** It needs no extra installation, keeps the very first
step focused on Python concepts (not tool concepts), and we can switch to
`uv` later in the project without much pain — it can adopt an existing venv
project.

## Diagram

```
papermind/
├── backend/
│   ├── .venv/              <- NEW, isolated Python env (gitignored)
│   ├── requirements.txt    <- NEW, empty for now — packages added as we need them
│   ├── notebooks/
│   │   └── (Phase 1 Step 2 will add the ingestion experiment notebook here)
│   └── src/
│       └── __init__.py     <- NEW, marks this as a Python package
```

## What we did

1. Created the `backend/` folder structure (`src/`, `notebooks/`, `requirements.txt`).
2. Created a virtual environment with the stdlib tool:
   ```
   cd backend
   python3 -m venv .venv
   ```
3. Confirmed `.venv/` and `venv/` are already covered by the repo's root `.gitignore`, so the environment itself never gets committed — only `requirements.txt` tracks what's installed.
