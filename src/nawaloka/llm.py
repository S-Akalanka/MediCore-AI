from langchain_openai import ChatOpenAI

from nawaloka.config import (
    API_KEY_ENV,
    LLM_MAX_TOKENS,
    LLM_REASONING_EFFORT,
    LLM_TEMPERATURE,
    PROVIDER_BASE_URL,
    get_model,
    get_secret,
)


def get_llm(role: str, json_mode: bool = False):
    """Build the chat model configured for an agent role."""
    llm = ChatOpenAI(
        model=get_model(role),
        base_url=PROVIDER_BASE_URL,
        api_key=get_secret(API_KEY_ENV),
        temperature=LLM_TEMPERATURE,
        max_tokens=LLM_MAX_TOKENS,
        reasoning_effort=LLM_REASONING_EFFORT,
    )
    if json_mode:
        return llm.bind(response_format={"type": "json_object"})
    return llm
