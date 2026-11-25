# 01 — LangChain LLM wrapper + 4-provider config switch

## What's about to happen

Phase 2 (vector store + retrieval) is done. Phase 3 adds the piece that
actually *answers* a question using the retrieved chunks: an LLM call. This
step doesn't build the full RAG answer chain yet (that needs prompts —
Phase 4) — it just builds the thing every later phase will sit on top of: a
single, swappable way to get a LangChain chat model, regardless of which
company's API is behind it.

1. Write one factory function that takes a provider name
   (`openai` / `anthropic` / `vertexai` / `bedrock`) and returns a ready-to-use
   LangChain chat model object.
2. Wire up and actually call **one** provider for real — OpenAI, since
   that's the one with an API key ready (originally planned as Vertex AI,
   switched before any code depended on it — OpenAI only needs a single
   key, no GCP project/service-account setup). The other three branches
   exist in the switch but raise a clear "not wired up yet" error until a
   later task fills them in — no point guessing at config shapes for APIs
   we haven't touched.
3. Demo it from a notebook: ask a real question, get a real (paid) answer
   back, print it.

## Why this way

**A factory function + config switch, not 4 separate call sites**
Every later phase (prompts, LangGraph workflow, FastAPI service) needs "the
current LLM" without caring which provider it is. If each of those phases
called `ChatOpenAI(...)` or `ChatVertexAI(...)` directly, switching
providers later would mean editing code in every one of them. One function,
`get_llm(provider)`, returning a LangChain `BaseChatModel`, means the rest
of the app only ever imports that function — switching providers becomes a
one-line change (which string gets passed in, eventually driven by a config
value / env var).

**Only OpenAI is actually wired up right now**
This is a deliberate, smaller slice of the full "4-provider switch" task:
wiring up and testing all four providers in one go would mean setting up
credentials for Anthropic, Vertex AI, and AWS Bedrock too, and spending
real money across all of them just to prove the switch shape works.
Proving it with one real provider is enough to validate the design; the
other three branches are stubbed with a `NotImplementedError` naming the
provider, so it's obvious (not silently broken) that they're not done yet,
and adding each one later is just filling in its branch.

**OpenAI via `langchain-openai`, key read from `.env`**
LangChain ships an official integration package per provider rather than
one mega-package. `langchain-openai`'s `ChatOpenAI` class reads
`OPENAI_API_KEY` from the environment automatically, so the only new thing
this step needs is that one secret, loaded from `backend/.env` (gitignored)
via `python-dotenv` — never hardcoded, never committed.

**Code lives in `backend/src/`, not another notebook-only experiment**
Every Phase 1/2 step lived entirely inside a notebook because each one was
a disposable experiment. This is the first piece meant to be *imported* by
later phases (Phase 4 prompts, Phase 5 LangGraph, Phase 6 FastAPI) — so the
factory function itself goes in `backend/src/llm/`, a real importable
module, while a notebook is still used to demo/verify it manually, the same
way the backend code will eventually be exercised by tests.

## Diagram

```
                      .env (OPENAI_API_KEY; future provider keys)
                               │
                               ▼
 get_llm("openai")    ──>  backend/src/llm/providers.py
 get_llm("anthropic")        │
 get_llm("vertexai")         ├── "openai"    ──> ChatOpenAI(...)  [wired + tested]
 get_llm("bedrock")          ├── "anthropic" ──> NotImplementedError
                             ├── "vertexai"  ──> NotImplementedError
                             └── "bedrock"   ──> NotImplementedError
                               │
                               ▼
                      LangChain BaseChatModel
                               │
                               ▼
                   notebook: llm.invoke("a real question")
```

## What we did

1. Added `backend/src/llm/providers.py` with `get_llm(provider, **kwargs)`:
   - `"openai"` → `ChatOpenAI` (reads `OPENAI_API_KEY` from `.env` via
     `python-dotenv`), model defaults to `gpt-4o-mini`.
   - `"anthropic"`, `"vertexai"`, `"bedrock"` → raise `NotImplementedError`.
2. Added `backend/notebooks/07_llm_provider_switch.ipynb`:
   - Confirmed all 4 provider names are recognized by the switch.
   - Confirmed the 3 unwired providers raise `NotImplementedError` cleanly.
   - Called `get_llm("openai").invoke(...)` for real and got back an actual
     answer: *"Retrieval-augmented generation is a process that combines
     the capabilities of information retrieval and natural language
     generation to enhance the quality of generated content by providing
     relevant context or data retrieved from external sources."*
3. One real hiccup along the way, worth recording: the first run hit
   `OpenAIRateLimitError: 429 — You have no credits remaining` — the key
   was valid, but the OpenAI account had no billing credit yet. Not a code
   bug; fixed by adding credit at platform.openai.com, then re-running.
4. Ended up switching the wired provider from the originally-planned
   Vertex AI to OpenAI mid-task, before any code was built against Vertex
   AI — swapped `langchain-google-vertexai` for `langchain-openai` in
   `requirements.txt`, and rewrote `.env.example` accordingly.
