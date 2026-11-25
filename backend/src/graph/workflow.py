from typing import TypedDict

from langchain_core.language_models import BaseChatModel
from langgraph.graph import END, StateGraph

from src.prompts import v3 as answer_prompt
from src.retrieval import RetrievalPipeline

NOT_FOUND_MESSAGE = (
    "I don't have enough information in the uploaded document to answer that."
)

GRADE_PROMPT = """Question: {question}

Retrieved context:
{context}

Does this context contain information that is actually relevant to \
answering the question? Reply with exactly one word: "yes" or "no"."""


class GraphState(TypedDict):
    question: str
    chunks: list[dict] | None
    answer: str | None
    grounded: bool | None


def build_graph(pipeline: RetrievalPipeline, llm: BaseChatModel):
    """Build the retrieve -> grade -> generate -> verify -> not_found graph.

    `pipeline` and `llm` are injected rather than constructed inside the
    nodes so the graph can be built once per process and reused across
    questions, and so tests/notebooks can swap in different pipelines or
    models without editing this module.
    """

    def retrieve(state: GraphState) -> GraphState:
        chunks = pipeline.retrieve(state["question"])
        return {**state, "chunks": chunks}

    def grade(state: GraphState) -> GraphState:
        context = "\n\n".join(chunk["text"] for chunk in state["chunks"])
        prompt = GRADE_PROMPT.format(question=state["question"], context=context)
        response = llm.invoke(prompt)
        relevant = "yes" in response.content.strip().lower()
        return {**state, "grounded": relevant}

    def route_after_grade(state: GraphState) -> str:
        return "generate" if state["grounded"] else "not_found"

    def generate(state: GraphState) -> GraphState:
        answer = answer_prompt.answer(state["question"], state["chunks"], llm)
        return {**state, "answer": answer}

    def verify(state: GraphState) -> GraphState:
        grounded = "(page" in state["answer"].lower()
        return {**state, "grounded": grounded}

    def route_after_verify(state: GraphState) -> str:
        return END if state["grounded"] else "not_found"

    def not_found(state: GraphState) -> GraphState:
        return {**state, "answer": NOT_FOUND_MESSAGE, "grounded": False}

    graph = StateGraph(GraphState)
    graph.add_node("retrieve", retrieve)
    graph.add_node("grade", grade)
    graph.add_node("generate", generate)
    graph.add_node("verify", verify)
    graph.add_node("not_found", not_found)

    graph.set_entry_point("retrieve")
    graph.add_edge("retrieve", "grade")
    graph.add_conditional_edges("grade", route_after_grade, {"generate": "generate", "not_found": "not_found"})
    graph.add_edge("generate", "verify")
    graph.add_conditional_edges("verify", route_after_verify, {END: END, "not_found": "not_found"})
    graph.add_edge("not_found", END)

    return graph.compile()
