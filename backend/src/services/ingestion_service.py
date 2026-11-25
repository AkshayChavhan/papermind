from pathlib import Path

from flask import Flask, jsonify, request
from werkzeug.utils import secure_filename

from src.retrieval import RetrievalPipeline

UPLOAD_DIR = Path("data/uploads")


def create_app(pipeline: RetrievalPipeline) -> Flask:
    """Build the Flask ingestion service. `pipeline` is injected so the
    same `RetrievalPipeline` instance can be shared with the FastAPI query
    service in tests/notebooks, instead of each service opening its own
    (local-mode Qdrant only allows one process to hold the storage file
    open at a time — see learning/08_api_services)."""
    app = Flask(__name__)

    @app.get("/health")
    def health():
        return jsonify({"status": "ok"})

    @app.post("/ingest")
    def ingest():
        if "file" not in request.files:
            return jsonify({"error": "missing 'file' in form-data"}), 400

        uploaded = request.files["file"]
        filename = secure_filename(uploaded.filename or "")
        if not filename:
            return jsonify({"error": "invalid filename"}), 400

        UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
        pdf_path = UPLOAD_DIR / filename
        uploaded.save(pdf_path)

        chunk_count = pipeline.ingest(pdf_path)
        return jsonify({"chunks": chunk_count})

    return app
