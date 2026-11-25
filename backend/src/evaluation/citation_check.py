import re

CITATION_PATTERN = re.compile(r"\(page\s+([\w.]+)\)", re.IGNORECASE)


def citation_precision(answer: str, chunks: list[dict]) -> float | None:
    """Of the page numbers the answer actually cites, what fraction
    correspond to a chunk that was really retrieved?

    Returns `None` when the answer has no citations at all (e.g. a
    refusal) — citation precision isn't a meaningful score for an answer
    that makes no citation claims in the first place.
    """
    cited_pages = {match.lower() for match in CITATION_PATTERN.findall(answer)}
    if not cited_pages:
        return None

    retrieved_pages = {chunk["page_label"].lower() for chunk in chunks}
    return len(cited_pages & retrieved_pages) / len(cited_pages)
