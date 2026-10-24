import json
import re
from dataclasses import dataclass

from langchain_core.messages import HumanMessage, SystemMessage
from loguru import logger

from nawaloka.engine.prompt import build_system_prompt
from nawaloka.llm import get_llm

UNCLEAR = "I could not understand that request. Could you rephrase it?"


@dataclass
class Generation:
    sql: str = ""
    clarification: str = ""


def _parse(content: str) -> Generation:
    match = re.search(r"\{.*\}", content, re.DOTALL)
    if not match:
        return Generation(clarification=UNCLEAR)
    try:
        data = json.loads(match.group(0))
    except json.JSONDecodeError:
        return Generation(clarification=UNCLEAR)
    return Generation(
        sql=(data.get("sql") or "").strip().rstrip(";"),
        clarification=(data.get("clarification") or "").strip(),
    )


def generate_sql(question: str, previous_sql: str = "", error: str = "") -> Generation:
    """Ask the LLM for a SQL query, optionally with feedback from a failed attempt."""
    user = question
    if previous_sql and error:
        user += f"\n\nYour previous query failed.\nQuery: {previous_sql}\nProblem: {error}\nReturn a corrected query."
    messages = [SystemMessage(content=build_system_prompt()), HumanMessage(content=user)]
    response = get_llm("sql_generator", json_mode=True).invoke(messages)
    logger.debug("LLM raw output: {}", response.content)
    return _parse(str(response.content))
