import json
import re

from langchain_core.messages import HumanMessage, SystemMessage
from loguru import logger

from nawaloka.agents.messages import RouterMessage
from nawaloka.llm import get_llm

INTENTS = {"data_query", "destructive", "out_of_scope", "unclear"}

SYSTEM_PROMPT = """You classify questions sent to the MediCore Hospital analytics assistant.
The database covers patients, doctors, specialties, appointments, admissions, diagnoses, lab orders, prescriptions, billing invoices, payments, departments and staff.

Choose one intent:
- data_query: a question that can be answered by reading hospital data
- destructive: asks to delete, update, insert, drop or otherwise change data
- out_of_scope: unrelated to hospital data, such as general knowledge or chit-chat
- unclear: gibberish or too vague to act on

Respond with JSON only: {"intent": "<intent>", "message": "<short reply to the user, empty for data_query>"}
"""


def classify(question: str) -> RouterMessage:
    """Classify the question into an intent. Defaults to data_query if the model fails."""
    try:
        response = get_llm("router", json_mode=True).invoke(
            [SystemMessage(content=SYSTEM_PROMPT), HumanMessage(content=question)]
        )
        match = re.search(r"\{.*\}", str(response.content), re.DOTALL)
        data = json.loads(match.group(0)) if match else {}
        intent = data.get("intent", "data_query")
        if intent not in INTENTS:
            intent = "data_query"
        return RouterMessage(intent=intent, message=(data.get("message") or "").strip())
    except Exception as exc:
        logger.warning("Router failed, defaulting to data_query: {}", exc)
        return RouterMessage(intent="data_query")
