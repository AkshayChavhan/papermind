"""Production entrypoint for the Flask ingestion service, run by PM2 as
`flask --app main_ingestion run`. Connects to a Qdrant *server*
(QDRANT_URL), the same instance `main_api.py` connects to, so documents
ingested here are immediately queryable there — this is the whole point
of server mode over local-mode. See learning/13_deployment for why."""

import os

from src.retrieval import RetrievalPipeline
from src.services import create_ingestion_app

QDRANT_URL = os.environ.get("QDRANT_URL", "http://localhost:6333")

pipeline = RetrievalPipeline(url=QDRANT_URL)
app = create_ingestion_app(pipeline)
