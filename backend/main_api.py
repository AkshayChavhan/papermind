"""Production entrypoint for the FastAPI query service, run by PM2/uvicorn
as `uvicorn main_api:app`. Unlike `run_api.py` (the local demo entrypoint),
this does NOT auto-ingest a sample PDF — real documents arrive through the
ingestion service's `/ingest` endpoint. Connects to a Qdrant *server*
(QDRANT_URL), not local-mode, so this process and the ingestion service can
run at the same time. See learning/13_deployment for why."""

import os

from src.retrieval import RetrievalPipeline
from src.services import create_query_app

QDRANT_URL = os.environ.get("QDRANT_URL", "http://localhost:6333")

pipeline = RetrievalPipeline(url=QDRANT_URL)
app = create_query_app(pipeline)
