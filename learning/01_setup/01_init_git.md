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

1. `git init` inside `papermind/`.
2. Added a `.gitignore` (OS junk, common dependency/build folders).
3. Committed everything currently in `papermind/` (CLAUDE.md, docs/, learning/) as the first commit.
