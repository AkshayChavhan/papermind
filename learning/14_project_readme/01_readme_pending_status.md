# 01 — Project README with a pending-status section

## What's about to happen

All 20 planned tasks are `Done` in `docs/TASKS.md`, and one follow-up
(task #21, verifying LangSmith tracing) closed the first of two
originally-pending items. Someone opening this repo cold has had no
single, top-level place to see "is this finished, and if not, what's
left" without digging into `docs/TASKS.md`, `docs/DEPLOYMENT.md`, and the
individual learning docs. This task adds a root `README.md` with a short
project summary and a **Pending** section that states plainly what still
needs the user's own action.

## Why this way

**A root README, not a new doc buried in `docs/` or `learning/`**
Every other status doc (`docs/TASKS.md`, `docs/DEPLOYMENT.md`) assumes
the reader is already inside the project's own documentation structure.
A root `README.md` is the one file GitHub renders on the repo's landing
page — the natural place for "what is this, how do I run it, what's
pending" for a first-time reader.

**Pending section points at the detailed docs instead of repeating them**
`docs/DEPLOYMENT.md` already has the full verified-vs-pending breakdown
for deployment. The README's job is to surface *that something is
pending* and link to where the detail lives, not to duplicate it and
risk the two drifting apart.

## What we did

1. Added root `README.md`: one-paragraph project description, pointers to
   `docs/TASKS.md`/`docs/ARCHITECTURE.md`/`docs/PROJECT_FLOW.md`, and a
   **Pending** section listing the one remaining blocked item (real VPS
   deployment — no SSH/VPS access available) with a link to
   `docs/DEPLOYMENT.md` for the exact steps.
2. Confirmed LangSmith is **not** listed as pending — it was verified
   working end-to-end in task #21 (real key, real logged run in the
   LangSmith `papermind` project).
3. Added a row to `docs/TASKS.md` for this task and linked this doc.
