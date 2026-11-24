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

**Loader: LlamaIndex's `SimpleDirectoryReader` / `PDFReader`**
Already the decided stack (see [ARCHITECTURE.md](../../docs/ARCHITECTURE.md)).
It reads a PDF page-by-page and keeps each page as its own `Document`, with
`page_label` in the metadata — that page number is what later becomes the
citation ("see page 4") the whole app is built around, so it has to survive
from the very first step.

**Chunker: `SentenceSplitter` (LlamaIndex), not a plain fixed-size splitter**
A dumb fixed-size splitter can cut a sentence in half mid-thought, which hurts
retrieval quality. `SentenceSplitter` breaks on sentence/paragraph boundaries
first and only falls back to a hard cut if a sentence itself is longer than
the chunk size. It also keeps the originating page's metadata on every chunk
it produces, so citations survive chunking too.

**Chunk size / overlap: 512 tokens / 50 token overlap (starting point)**
512 is a common starting chunk size for RAG — big enough to hold a full idea,
small enough to stay cheap to embed and precise to retrieve. A 50-token
overlap means an idea split across a chunk boundary still appears whole in at
least one chunk. Both are easy to tune later once Phase 2 adds retrieval and
we can measure answer quality, not just guess.

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

1. Activated `backend/.venv` and installed the first real packages:
   `llama-index-core`, `llama-index-readers-file`, `pypdf` (PDF parsing),
   `reportlab` (sample-PDF generation), `jupyter` + `ipykernel` (to run the
   notebook). `requirements.txt` now pins these versions.
2. Added `backend/notebooks/generate_sample_pdf.py` — builds a throwaway
   4-page PDF (abstract/intro/method/results) under
   `backend/notebooks/data/` (gitignored, regenerated each run).
3. Added `backend/notebooks/01_pdf_ingestion.ipynb`:
   - Loads the sample PDF with `PDFReader` → 4 page-`Document`s, each
     carrying `metadata["page_label"]`.
   - Splits them with `SentenceSplitter(chunk_size=512, chunk_overlap=50)`
     → one chunk per page at this size (the sample pages are short; longer
     real papers will show multi-chunk pages and cross-page overlap).
   - Confirmed `page_label` metadata survives onto every chunk.
4. Executed the notebook in place (`jupyter nbconvert --execute`) so it's
   committed with real output, not empty cells.
