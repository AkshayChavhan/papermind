# How Things Flow

Two kinds of "flow" live here: how *we work* on this project (settled now), and how *the system itself* will move data (filled in once something is built).

## 1. How we work on a task

```
 ┌──────────────┐   ┌───────────────────┐   ┌──────────┐   ┌────────────────┐   ┌──────────────┐
 │ Pick a task  │ → │ Write learning doc │ → │ Do the   │ → │ Recheck doc,    │ → │ Mark task     │
 │              │   │ (what + why)       │   │ work     │   │ ask you confirm │   │ Done in TASKS │
 └──────────────┘   └───────────────────┘   └──────────┘   └────────────────┘   └──────────────┘
```

1. **Pick a task** — gets a row in [TASKS.md](./TASKS.md) with status `Todo`.
2. **Write the learning doc first** — before touching code, a short doc goes in `learning/<topic>/NN_description.md` explaining what we're about to do and why.
3. **Do the work.**
4. **Recheck** — compare the doc to what actually happened, fix anything that drifted, then ask you to confirm it's correct and makes sense. Any correction you give gets folded straight into the doc.
5. **Mark it done** — status flips to `Done` in TASKS.md.

## 2. How the system itself flows

> Not written yet — there's no architecture to trace. Once [ARCHITECTURE.md](./ARCHITECTURE.md) has real pieces in it, this section becomes a diagram of how a request/piece of data moves through them (e.g. user → frontend → API → database).
