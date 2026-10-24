from langchain_core.messages import HumanMessage, SystemMessage
from loguru import logger

from nawaloka.llm import get_llm

STATIC_MESSAGE = (
    "I could not answer that. Try asking about patients, doctors, appointments, admissions, "
    "billing or payments, for example: Which doctors have the highest no-show rates?"
)

SYSTEM_PROMPT = """You help users of a hospital analytics assistant after their question could not be answered.
In 2 sentences, explain in plain language that the question could not be answered, then suggest one concrete way to rephrase it.
Do not mention SQL, errors or databases."""


def respond(question: str) -> str:
    """Return a friendly message for a question the pipeline could not answer."""
    try:
        response = get_llm("fallback").invoke(
            [SystemMessage(content=SYSTEM_PROMPT), HumanMessage(content=question)]
        )
        text = str(response.content).strip()
        return text or STATIC_MESSAGE
    except Exception as exc:
        logger.warning("Fallback agent failed, using static message: {}", exc)
        return STATIC_MESSAGE
