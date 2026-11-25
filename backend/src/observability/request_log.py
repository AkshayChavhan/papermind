import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

DEFAULT_LOG_PATH = Path("data/logs/requests.jsonl")


def log_request(question: str, result: dict[str, Any], duration_s: float, log_path: Path = DEFAULT_LOG_PATH) -> dict:
    """Append one structured JSON line describing a graph call."""
    record = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "question": question,
        "pages": [chunk["page_label"] for chunk in (result.get("chunks") or [])],
        "grounded": result.get("grounded"),
        "answer_length": len(result.get("answer") or ""),
        "duration_s": round(duration_s, 3),
    }
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with open(log_path, "a") as log_file:
        log_file.write(json.dumps(record) + "\n")
    return record


def timed_invoke(graph, question: str, log_path: Path = DEFAULT_LOG_PATH) -> dict:
    """Run `graph.invoke` and log the call. Used by the FastAPI /ask route
    so every real request gets logged, not just notebook runs."""
    start = time.perf_counter()
    result = graph.invoke({"question": question})
    duration_s = time.perf_counter() - start
    log_request(question, result, duration_s, log_path=log_path)
    return result
