from fastapi import FastAPI
from pydantic import BaseModel

from src.graph import build_graph
from src.llm import get_llm
from src.observability import timed_invoke
from src.retrieval import RetrievalPipeline


class AskRequest(BaseModel):
    question: str


class AskResponse(BaseModel):
    answer: str
    grounded: bool
    pages: list[str]


def create_app(pipeline: RetrievalPipeline, provider: str = "openai") -> FastAPI:
    """Build the FastAPI query service. `pipeline` is injected for the same
    reason as the Flask ingestion service — see
    learning/08_api_services. The graph is built once here, not per
    request, so the LLM client isn't recreated on every call."""
    llm = get_llm(provider)
    graph = build_graph(pipeline, llm)

    app = FastAPI(title="papermind query service")

    @app.get("/health")
    def health():
        return {"status": "ok"}

    @app.post("/ask", response_model=AskResponse)
    def ask(request: AskRequest) -> AskResponse:
        result = timed_invoke(graph, request.question)
        pages = [chunk["page_label"] for chunk in (result["chunks"] or [])]
        return AskResponse(answer=result["answer"], grounded=bool(result["grounded"]), pages=pages)

    return app
