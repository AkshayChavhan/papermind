from langchain_core.language_models import BaseChatModel

PROMPT_TEMPLATE = """Context:
{context}

Question: {question}

Answer the question using the context above."""


def build_prompt(question: str, chunks: list[dict]) -> str:
    context = "\n\n".join(chunk["text"] for chunk in chunks)
    return PROMPT_TEMPLATE.format(context=context, question=question)


def answer(question: str, chunks: list[dict], llm: BaseChatModel) -> str:
    prompt = build_prompt(question, chunks)
    response = llm.invoke(prompt)
    return response.content
