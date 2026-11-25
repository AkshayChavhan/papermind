from dotenv import load_dotenv
from langchain_core.language_models import BaseChatModel

load_dotenv()

SUPPORTED_PROVIDERS = ("openai", "anthropic", "vertexai", "bedrock")


def get_llm(provider: str, **kwargs) -> BaseChatModel:
    """Return a LangChain chat model for the given provider.

    Only "openai" is wired up so far; the others raise NotImplementedError
    until a later task fills in their branch.
    """
    if provider not in SUPPORTED_PROVIDERS:
        raise ValueError(f"Unknown provider {provider!r}; expected one of {SUPPORTED_PROVIDERS}")

    if provider == "openai":
        from langchain_openai import ChatOpenAI

        return ChatOpenAI(model=kwargs.pop("model", "gpt-4o-mini"), **kwargs)

    raise NotImplementedError(f"Provider {provider!r} is not wired up yet")
