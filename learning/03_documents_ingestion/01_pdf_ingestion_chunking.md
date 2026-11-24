# 01 — PDF ingestion + chunking

## What's about to happen

This is Phase 1 · Step 2 of papermind. Step 1 built the `backend/` folder and
an empty virtual environment but never activated it or installed anything.
This step:

1. Activates `backend/.venv` and installs the first real packages
   (`requirements.txt` stops being empty).
2. Loads a PDF into text using a LlamaIndex reader.
3. Splits that text into overlapping chunks — the unit we'll eventually embed
   and search over in Phase 2.
4. All of this happens in a notebook (`backend/notebooks/01_pdf_ingestion.ipynb`),
   matching the experiment-first pattern the Step 1 doc already set up.

No sample research paper is committed to the repo (keeps it clear of binary
files). A tiny script generates a throwaway multi-page PDF locally instead,
so the experiment is fully reproducible from code alone.

## Why this way

**Loader: LlamaIndex's `PDFReader`**
Keeps each page as its own `Document` with a `page_label`, so page-number citations survive from day one.

**Chunker: `SentenceSplitter`, not fixed-size**
Breaks on sentence boundaries instead of cutting mid-thought, and carries each chunk's page metadata forward too.

**Chunk size / overlap: 512 / 50 tokens**
A common RAG starting point — big enough per idea, cheap to embed, overlap keeps split ideas whole; tunable later.

## Diagram

```
 generate_sample_pdf.py
         │
         ▼
   sample.pdf (local, gitignored)
         │
         ▼  PDFReader
 ┌─────────────────────┐
 │ Document (page 1)   │  metadata: {page_label: "1"}
 │ Document (page 2)   │  metadata: {page_label: "2"}
 │ ...                  │
 └─────────────────────┘
         │
         ▼  SentenceSplitter (512 tokens, 50 overlap)
 ┌─────────────────────┐
 │ Chunk 1  (page 1)   │
 │ Chunk 2  (page 1-2)  │
 │ Chunk 3  (page 2)   │
 │ ...                  │
 └─────────────────────┘
         │
         ▼
 (Phase 2 will embed these into Qdrant)
```

## What we did

1. Activated the venv Step 1 created, and installed the first real packages
   into it:
   ```
   cd backend
   source .venv/bin/activate
   pip install llama-index-core llama-index-readers-file pypdf reportlab jupyter ipykernel
   ```
   `requirements.txt` now pins the installed versions, one per line, with a
   short comment on what each package is for:
   `llama-index-core` (loader + chunking framework), `llama-index-readers-file`
   (PDF page reader), `pypdf` (the PDF parser underneath), `reportlab`
   (generates the sample test PDF below), `jupyter` (the notebook interface —
   shows cells and their output) and `ipykernel` (the engine that actually
   runs the Python inside those cells — see "Why a notebook" below).
2. Added `backend/notebooks/generate_sample_pdf.py` — a script that builds a
   throwaway 4-page PDF (abstract/intro/method/results) so the notebook has
   something to load without a real paper committed to the repo:
   ```
   python notebooks/generate_sample_pdf.py
   # -> backend/notebooks/data/sample.pdf (gitignored, regenerated on demand)
   ```
3. Added `backend/notebooks/01_pdf_ingestion.ipynb`:
   - Loads the sample PDF with `PDFReader` → 4 page-`Document`s, each
     carrying `metadata["page_label"]`.
   - Splits them with `SentenceSplitter(chunk_size=512, chunk_overlap=50)`
     → one chunk per page at this size (the sample pages are short; longer
     real papers will show multi-chunk pages and cross-page overlap).
   - Confirmed `page_label` metadata survives onto every chunk.
4. Ran the whole notebook from the terminal, writing real output back into
   the file (so it's committed already-run, not empty cells):
   ```
   jupyter nbconvert --to notebook --execute --inplace notebooks/01_pdf_ingestion.ipynb
   ```

## Why a notebook (not just a script)?

Jupyter and ipykernel split into two jobs: **Jupyter** is the notebook
itself — the boxes ("cells") you write code in and see the result printed
right underneath, like a dining room where you sit. **ipykernel** is what
actually *runs* that Python code when you execute a cell — the kitchen/chef
behind the scenes, which also remembers variables from earlier cells. Jupyter
without ipykernel would just be an empty room with a "Run" button that does
nothing.

We used a notebook here (instead of a plain `.py` script) because this step
is exploration, not production code: trying the loader, checking what a
`Document`'s metadata looks like, tuning chunk size — all things that are
easier to see step-by-step with output under each step, rather than running
a whole script and only seeing the final `print`. Once this logic is solid,
Phase 6's FastAPI/Flask services will reimplement it as plain reusable
Python — no notebook, no Jupyter, no ipykernel needed at that point.
