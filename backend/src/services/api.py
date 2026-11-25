import json

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from src.graph import build_graph, stream_answer
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
    app.add_middleware(
        CORSMiddleware,
        allow_origin_regex=r"http://localhost:\d+",
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/health")
    def health():
        return {"status": "ok"}

    @app.post("/ask", response_model=AskResponse)
    def ask(request: AskRequest) -> AskResponse:
        result = timed_invoke(graph, request.question)
        pages = [chunk["page_label"] for chunk in (result["chunks"] or [])]
        return AskResponse(answer=result["answer"], grounded=bool(result["grounded"]), pages=pages)

    @app.post("/ask/stream")
    def ask_stream(request: AskRequest) -> StreamingResponse:
        def event_source():
            for event in stream_answer(pipeline, llm, request.question):
                yield f"data: {json.dumps(event)}\n\n"

        return StreamingResponse(event_source(), media_type="text/event-stream")

    return app
