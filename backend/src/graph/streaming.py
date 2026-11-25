from collections.abc import Iterator

from langchain_core.language_models import BaseChatModel

from src.graph.workflow import GRADE_PROMPT, NOT_FOUND_MESSAGE
from src.prompts import v3 as answer_prompt
from src.retrieval import RetrievalPipeline


def stream_answer(pipeline: RetrievalPipeline, llm: BaseChatModel, question: str) -> Iterator[dict]:
    """Generator version of the Phase 5 graph's retrieve->grade->generate
    path, streaming the `generate` step's tokens live instead of returning
    one final blocking result. A parallel path to `build_graph()`, not a
    rewrite of it — see learning/12_nextjs_chat_ui for why.

    Yields `{"type": "token", "text": ...}` events while the answer is
    generated, then exactly one `{"type": "done", "answer", "grounded",
    "pages"}` event at the end.
    """
    chunks = pipeline.retrieve(question)
    pages = [chunk["page_label"] for chunk in chunks]

    context = "\n\n".join(chunk["text"] for chunk in chunks)
    grade_response = llm.invoke(GRADE_PROMPT.format(question=question, context=context))
    relevant = "yes" in grade_response.content.strip().lower()

    if not relevant:
        yield {"type": "done", "answer": NOT_FOUND_MESSAGE, "grounded": False, "pages": pages}
        return

    prompt = answer_prompt.build_prompt(question, chunks)
    full_answer = ""
    for token_chunk in llm.stream(prompt):
        token = token_chunk.content
        if token:
            full_answer += token
            yield {"type": "token", "text": token}

    grounded = "(page" in full_answer.lower()
    yield {
        "type": "done",
        "answer": full_answer if grounded else NOT_FOUND_MESSAGE,
        "grounded": grounded,
        "pages": pages,
    }
