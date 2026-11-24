"""Generate a throwaway multi-page PDF so the ingestion notebook has
something to load without committing a binary file to the repo."""

from pathlib import Path

from reportlab.lib.pagesizes import LETTER
from reportlab.pdfgen import canvas

OUTPUT_PATH = Path(__file__).parent / "data" / "sample.pdf"

PAGES = [
    (
        "Abstract",
        "This paper studies retrieval-augmented generation for question "
        "answering over research papers. We show that combining dense "
        "retrieval with a re-ranking stage improves citation accuracy "
        "compared to retrieval alone.",
    ),
    (
        "1. Introduction",
        "Large language models can answer questions fluently but often "
        "fabricate details not present in the source document. Grounding "
        "each answer in retrieved passages, and citing the page each "
        "passage came from, lets a reader verify the answer directly.",
    ),
    (
        "2. Method",
        "Documents are split into overlapping chunks of roughly five "
        "hundred tokens. Each chunk is embedded and stored alongside the "
        "page number it was extracted from, so retrieval results can "
        "always be traced back to a specific page in the original PDF.",
    ),
    (
        "3. Results",
        "Across a held-out set of research papers, grounded answers with "
        "page citations were rated as more trustworthy than ungrounded "
        "answers by human reviewers, even when the two answers conveyed "
        "the same information.",
    ),
]


def generate() -> Path:
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    c = canvas.Canvas(str(OUTPUT_PATH), pagesize=LETTER)
    for heading, body in PAGES:
        c.setFont("Helvetica-Bold", 14)
        c.drawString(72, 740, heading)
        c.setFont("Helvetica", 11)
        text_object = c.beginText(72, 710)
        text_object.setLeading(16)
        for line in _wrap(body, width=90):
            text_object.textLine(line)
        c.drawText(text_object)
        c.showPage()
    c.save()
    return OUTPUT_PATH


def _wrap(text: str, width: int) -> list[str]:
    words = text.split()
    lines, current = [], ""
    for word in words:
        if len(current) + len(word) + 1 > width:
            lines.append(current)
            current = word
        else:
            current = f"{current} {word}".strip()
    if current:
        lines.append(current)
    return lines


if __name__ == "__main__":
    path = generate()
    print(f"Wrote {path}")
