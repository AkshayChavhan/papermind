"""Run the FastAPI query service standalone, ingesting the sample PDF on
startup so there's something to ask about. `python run_api.py`."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "notebooks"))

import uvicorn
from generate_sample_pdf import generate

from src.retrieval import RetrievalPipeline
from src.services import create_query_app

if __name__ == "__main__":
    pdf_path = generate()
    pipeline = RetrievalPipeline(storage_path=Path("data/qdrant_api"))
    pipeline.ingest(pdf_path)

    app = create_query_app(pipeline)
    uvicorn.run(app, host="0.0.0.0", port=8000)
