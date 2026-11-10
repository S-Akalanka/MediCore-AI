import json
import re

from langchain_core.messages import HumanMessage, SystemMessage
from loguru import logger

from nawaloka.llm import get_llm

MAX_TURNS = 5

SYSTEM_PROMPT = """You rewrite follow-up questions in a hospital analytics chat so they can be understood on their own.
You receive the previous turns and the new question.
Only use the earlier turns when the new question clearly depends on them, for example "what about last year?", "only for cardiology" or "show that as a pie chart". In that case rewrite it as one complete standalone question and keep any requested chart type.
A question that stands on its own, even if it is vague, must be returned unchanged. Never answer the question.

Respond with JSON only: {"question": "<standalone question>"}
"""


class Memory:
    """Keeps the most recent turns of a conversation."""

    def __init__(self, max_turns: int = MAX_TURNS) -> None:
        self.max_turns = max_turns
        self.turns: list[dict[str, str]] = []

    def add(self, question: str, sql: str, answer: str) -> None:
        """Store one completed turn and drop the oldest if over the limit."""
        self.turns.append({"question": question, "sql": sql, "answer": answer})
        self.turns = self.turns[-self.max_turns :]

    def clear(self) -> None:
        self.turns = []


def rewrite(question: str, history: list[dict[str, str]]) -> str:
    """Return a standalone version of the question, or the original if rewriting fails."""
    if not history:
        return question
    lines = [f"Q: {t['question']}\nSQL: {t['sql']}\nA: {t['answer']}" for t in history[-MAX_TURNS:]]
    payload = "Previous turns:\n" + "\n\n".join(lines) + f"\n\nNew question: {question}"
    try:
        response = get_llm("router", json_mode=True).invoke(
            [SystemMessage(content=SYSTEM_PROMPT), HumanMessage(content=payload)]
        )
        match = re.search(r"\{.*\}", str(response.content), re.DOTALL)
        data = json.loads(match.group(0)) if match else {}
        return (data.get("question") or "").strip() or question
    except Exception as exc:
        logger.warning("Contextualizer failed, using original question: {}", exc)
        return question
