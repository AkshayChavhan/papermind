# 01 — Initializing git for papermind

## What's about to happen

We're turning `papermind/` into its own git repository, so every future task's
changes get committed with a message explaining what and why.

## Why this way

The parent folder (`Desktop/Projects/Project/`) already has an *empty* git
repo at its root. Using that one would be a problem: it would start tracking
every unrelated sibling folder in there too (go-mechanic, job_finder,
mirror-ai, ...), not just papermind. Since papermind is meant to be its own
project with its own clean history, we instead run `git init` *inside*
`papermind/` itself. Git supports a repo nested inside another repo's
directory tree — git only looks at the nearest `.git` folder going up from
wherever a command runs, so commands run from inside `papermind/` will use
papermind's own `.git`, and the parent repo (if it's ever used) would just
see `papermind/` as an untracked subfolder, not reach inside it.

We also add a `.gitignore` so editor/OS junk (`.DS_Store`, etc.) and any
future dependency folders (`node_modules/`, `.venv/`, etc.) never get
committed by accident.

## Diagram

```
Desktop/Projects/Project/        <- parent folder, has its own (empty) .git
├── .git/                        <- parent repo — we leave this alone
├── go-mechanic/                 <- unrelated sibling project
├── job_finder/                  <- unrelated sibling project
└── papermind/
    ├── .git/                    <- NEW: papermind's own repo, scoped to just this folder
    ├── .gitignore                <- NEW
    ├── CLAUDE.md
    ├── docs/
    └── learning/
```

## What we did

1. Checked the existing state before touching anything:
   ```
   git status
   git rev-parse --show-toplevel
   git rev-parse --git-dir
   ```
   This is what revealed the parent folder's empty repo and its toplevel at
   `Project/` instead of `papermind/`.
2. Added a `.gitignore` (OS junk, common dependency/build folders).
3. Initialized papermind's own repo and confirmed it was scoped correctly:
   ```
   git init
   git rev-parse --show-toplevel   # -> .../papermind
   git rev-parse --git-dir          # -> .git (papermind's own)
   git status                       # only papermind's own files show up
   ```
4. Staged and committed everything currently in `papermind/` (`.gitignore`, `CLAUDE.md`, `docs/`, `learning/`) as the first commit:
   ```
   git add .gitignore CLAUDE.md docs learning
   git commit -m "Initialize papermind as its own git repo ..."
   git log --oneline
   ```
5. Renamed the `setup` learning topic to `01_setup` and updated its references:
   ```
   git mv learning/setup learning/01_setup
   git add -A
   git commit -m "Number the learning topic folder: setup -> 01_setup ..."
   git log --oneline
   ```
