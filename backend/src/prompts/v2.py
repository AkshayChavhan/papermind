from langchain_core.language_models import BaseChatModel

PROMPT_TEMPLATE = """Context:
{context}

Question: {question}

Answer using only the context above. Cite the page number for every claim, \
e.g. (page 4). If different parts of the context come from different \
pages, cite each page separately."""


def build_prompt(question: str, chunks: list[dict]) -> str:
    context = "\n\n".join(f"(page {chunk['page_label']})\n{chunk['text']}" for chunk in chunks)
    return PROMPT_TEMPLATE.format(context=context, question=question)


def answer(question: str, chunks: list[dict], llm: BaseChatModel) -> str:
    prompt = build_prompt(question, chunks)
    response = llm.invoke(prompt)
    return response.content
