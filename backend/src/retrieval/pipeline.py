from pathlib import Path
from uuid import NAMESPACE_URL, uuid5

from fastembed import SparseTextEmbedding, TextEmbedding
from fastembed.rerank.cross_encoder import TextCrossEncoder
from llama_index.core.node_parser import SentenceSplitter
from llama_index.readers.file import PDFReader
from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    Fusion,
    FusionQuery,
    Modifier,
    PointStruct,
    Prefetch,
    SparseVector,
    SparseVectorParams,
    VectorParams,
)

COLLECTION_NAME = "papermind_chunks"
DENSE_MODEL = "BAAI/bge-small-en-v1.5"
SPARSE_MODEL = "Qdrant/bm25"
RERANK_MODEL = "Xenova/ms-marco-MiniLM-L-6-v2"
FETCH_LIMIT = 4
TOP_K = 2


class RetrievalPipeline:
    """Owns the embedders, reranker and Qdrant client, and knows how to
    ingest a PDF and retrieve+rerank chunks for a question.

    One instance per process: the embedding/rerank models are expensive to
    load, so callers (e.g. the LangGraph workflow in src/graph) build one
    instance and reuse it across every call instead of reloading models
    per question.
    """

    def __init__(self, storage_path: Path, collection_name: str = COLLECTION_NAME):
        self.client = QdrantClient(path=str(storage_path))
        self.collection_name = collection_name
        self.dense_embedder = TextEmbedding(model_name=DENSE_MODEL)
        self.sparse_embedder = SparseTextEmbedding(model_name=SPARSE_MODEL)
        self.reranker = TextCrossEncoder(model_name=RERANK_MODEL)

    def ingest(self, pdf_path: Path) -> int:
        """(Re)build the collection from a single PDF. Returns chunk count."""
        documents = PDFReader().load_data(file=pdf_path)
        splitter = SentenceSplitter(chunk_size=512, chunk_overlap=50)
        nodes = splitter.get_nodes_from_documents(documents)

        if self.client.collection_exists(self.collection_name):
            self.client.delete_collection(self.collection_name)
        self.client.create_collection(
            collection_name=self.collection_name,
            vectors_config={"dense": VectorParams(size=384, distance=Distance.COSINE)},
            sparse_vectors_config={"bm25": SparseVectorParams(modifier=Modifier.IDF)},
        )

        texts = [node.get_content() for node in nodes]
        dense_vectors = list(self.dense_embedder.embed(texts))
        sparse_vectors = list(self.sparse_embedder.embed(texts))

        page_counters: dict[str, int] = {}
        points = []
        for node, dense_vector, sparse_vector in zip(nodes, dense_vectors, sparse_vectors):
            page_label = node.metadata["page_label"]
            file_name = node.metadata["file_name"]
            chunk_index = page_counters.get(page_label, 0)
            page_counters[page_label] = chunk_index + 1

            point_id = str(uuid5(NAMESPACE_URL, f"{file_name}:{page_label}:{chunk_index}"))
            points.append(
                PointStruct(
                    id=point_id,
                    vector={
                        "dense": dense_vector.tolist(),
                        "bm25": SparseVector(
                            indices=sparse_vector.indices.tolist(),
                            values=sparse_vector.values.tolist(),
                        ),
                    },
                    payload={
                        "text": node.get_content(),
                        "page_label": page_label,
                        "file_name": file_name,
                        "chunk_index": chunk_index,
                    },
                )
            )

        self.client.upsert(collection_name=self.collection_name, points=points)
        return len(points)

    def retrieve(self, question: str, top_k: int = TOP_K, fetch_limit: int = FETCH_LIMIT) -> list[dict]:
        """Hybrid search (dense + bm25, RRF-fused) over-fetching
        `fetch_limit` candidates, then cross-encoder re-rank down to
        `top_k`. Returns a list of chunk payloads."""
        query_dense = next(self.dense_embedder.embed([question])).tolist()
        query_sparse = next(self.sparse_embedder.embed([question]))

        hybrid_response = self.client.query_points(
            collection_name=self.collection_name,
            prefetch=[
                Prefetch(query=query_dense, using="dense", limit=10),
                Prefetch(
                    query=SparseVector(
                        indices=query_sparse.indices.tolist(),
                        values=query_sparse.values.tolist(),
                    ),
                    using="bm25",
                    limit=10,
                ),
            ],
            query=FusionQuery(fusion=Fusion.RRF),
            limit=fetch_limit,
            with_payload=True,
        )
        candidates = hybrid_response.points
        candidate_texts = [c.payload["text"] for c in candidates]
        rerank_scores = list(self.reranker.rerank(question, candidate_texts))
        scored = sorted(zip(candidates, rerank_scores), key=lambda pair: pair[1], reverse=True)
        return [c.payload for c, _ in scored[:top_k]]
