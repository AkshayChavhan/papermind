# 01 — Initializing git for papermind

## What's about to happen

We're turning `papermind/` into its own git repository, so every future
task's changes get committed with a message explaining what and why.

## Why this way

papermind is its own project, so it gets its own repo with its own clean
history — separate from whatever else lives alongside it on disk. We also
add a `.gitignore` so editor/OS junk (`.DS_Store`, etc.) and any future
dependency folders (`node_modules/`, `.venv/`, etc.) never get committed by
accident.

## Diagram

```
papermind/
├── .git/          <- NEW: papermind's own repo
├── .gitignore     <- NEW
├── CLAUDE.md
├── docs/
└── learning/
```

## What we did

1. Added a `.gitignore` (OS junk, common dependency/build folders).
2. Initialized the repo and checked it:
   ```
   git init
   git rev-parse --show-toplevel   # -> .../papermind
   git rev-parse --git-dir          # -> .git
   git status
   ```
3. Staged and committed everything currently in `papermind/` (`.gitignore`, `CLAUDE.md`, `docs/`, `learning/`) as the first commit:
   ```
   git add .gitignore CLAUDE.md docs learning
   git commit -m "Initialize papermind as its own git repo ..."
   git log --oneline
   ```
4. Renamed the learning topic `setup` to `01_setup`, then to `01_repo_setup` (more specific), updating references each time:
   ```
   git mv learning/setup learning/01_setup
   git add -A
   git commit -m "Number the learning topic folder: setup -> 01_setup ..."

   git mv learning/01_setup learning/01_repo_setup
   git add -A
   git commit -m "Rename learning topic: 01_setup -> 01_repo_setup ..."
   ```
