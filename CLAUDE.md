# CLAUDE.md — papermind

This project exists to learn how to build things to a high engineering standard — the documentation trail matters as much as the code.

## Rules for every task

1. **Before starting**, write/update a learning doc at `learning/<topic>/NN_description.md` (topics: `setup`, `frontend`, `backend`, `documents`, `rag-pipeline`, etc. — add topics as needed) explaining what's about to happen and why. Keep it short, plain language, add a diagram if it helps.
2. Do the work.
3. **After finishing**, recheck the doc against what actually happened, update it if it drifted, then ask the user to confirm it's correct / makes sense. Fold in any correction immediately.
4. Update [`docs/TASKS.md`](docs/TASKS.md): move the task's status to `Done`.
5. Keep [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) and [`docs/PROJECT_FLOW.md`](docs/PROJECT_FLOW.md) current whenever a task changes the system's structure or how data moves through it.

See [`docs/PROJECT_FLOW.md`](docs/PROJECT_FLOW.md) for the full picture of this loop.

## Git rules

1. **Never commit without asking first.** Always get explicit permission from the user before running `git commit` (or `git push`), even if the rest of the task is already approved.
2. **Commit message format:** use the related learning doc's path, with `/` replaced by `_` and the `.md` dropped — e.g. a doc at `learning/01_repo_setup/01_init_git.md` commits as:
   ```
    01_repo_setup_01_init_git_<description_of_ticket_in_10_words>
   ```
