import operator
from time import perf_counter
from typing import Annotated, Any, Callable, TypedDict

from langgraph.graph import END, StateGraph
from loguru import logger

from nawaloka.agents import fallback, interpreter, router
from nawaloka.agents.messages import Interpretation, PipelineResult, RouterMessage, StepTrace
from nawaloka.engine.engine import EngineResult, ask
from nawaloka.observability import observed, record_io, start_usage, stop_usage
from nawaloka.traces import save_trace


class PipelineState(TypedDict, total=False):
    question: str
    router: RouterMessage
    sql_result: EngineResult
    interpretation: Interpretation
    status: str
    answer: str
    error: str
    steps: Annotated[list[StepTrace], operator.add]


def _traced(name: str, fn: Callable[[PipelineState], dict[str, Any]]):
    @observed(name)
    def run(state: PipelineState) -> dict[str, Any]:
        update = fn(state)
        output = {"status": update.get("status", ""), "answer": update.get("answer", "")}
        if "sql_result" in update:
            output["sql"] = update["sql_result"].sql
            output["row_count"] = len(update["sql_result"].rows)
        record_io({"question": state["question"]}, output)
        return update

    def wrapper(state: PipelineState) -> dict[str, Any]:
        start = perf_counter()
        token = start_usage()
        try:
            update = run(state)
            status, detail = "ok", update.get("status", "")
        except Exception as exc:
            logger.error("Agent {} crashed: {}", name, exc)
            update, status, detail = {"error": f"{name}: {exc}"}, "error", str(exc)
        usage = stop_usage(token)
        step = StepTrace(
            name, status, round((perf_counter() - start) * 1000, 1), detail, usage["input"], usage["output"]
        )
        return {**update, "steps": [step]}

    return wrapper


def _router_node(state: PipelineState) -> dict[str, Any]:
    return {"router": router.classify(state["question"])}


def _direct_node(state: PipelineState) -> dict[str, Any]:
    message = state["router"]
    status = {"destructive": "blocked", "unclear": "clarification"}.get(message.intent, "out_of_scope")
    default = "I can only answer questions about hospital data."
    return {"status": status, "answer": message.message or default}


def _sql_node(state: PipelineState) -> dict[str, Any]:
    result = ask(state["question"])
    return {"sql_result": result, "status": result.status}


def _sql_done_node(state: PipelineState) -> dict[str, Any]:
    result = state["sql_result"]
    return {"status": result.status, "answer": result.message}


def _interpret_node(state: PipelineState) -> dict[str, Any]:
    result = state["sql_result"]
    interpretation = interpreter.interpret(state["question"], result.sql, result.rows)
    return {"interpretation": interpretation, "status": "ok", "answer": interpretation.summary}


def _fallback_node(state: PipelineState) -> dict[str, Any]:
    return {"status": "fallback", "answer": fallback.respond(state["question"])}


def _after_router(state: PipelineState) -> str:
    message = state.get("router")
    if message is None or message.intent == "data_query":
        return "sql"
    return "direct"


def _after_sql(state: PipelineState) -> str:
    if state.get("error"):
        return "fallback"
    status = state["sql_result"].status
    if status == "ok":
        return "interpret"
    if status == "failed":
        return "fallback"
    return "sql_done"


def build_graph():
    """Compile the router, SQL, interpreter and fallback agents into one graph."""
    graph = StateGraph(PipelineState)
    graph.add_node("router", _traced("router", _router_node))
    graph.add_node("direct", _traced("direct", _direct_node))
    graph.add_node("sql", _traced("sql_generator", _sql_node))
    graph.add_node("sql_done", _traced("sql_done", _sql_done_node))
    graph.add_node("interpret", _traced("interpreter", _interpret_node))
    graph.add_node("fallback", _traced("fallback", _fallback_node))
    graph.set_entry_point("router")
    graph.add_conditional_edges("router", _after_router, {"sql": "sql", "direct": "direct"})
    graph.add_conditional_edges(
        "sql",
        _after_sql,
        {"interpret": "interpret", "fallback": "fallback", "sql_done": "sql_done"},
    )
    for node in ("direct", "sql_done", "interpret", "fallback"):
        graph.add_edge(node, END)
    return graph.compile()


_graph = None


@observed("nawaloka-pipeline")
def _run(question: str) -> PipelineResult:
    global _graph
    if _graph is None:
        _graph = build_graph()
    try:
        state = _graph.invoke({"question": question, "steps": []})
    except Exception as exc:
        logger.error("Pipeline crashed: {}", exc)
        return PipelineResult(question, "fallback", answer=fallback.STATIC_MESSAGE)

    sql_result = state.get("sql_result")
    result = PipelineResult(
        question=question,
        status=state.get("status", "fallback"),
        answer=state.get("answer", fallback.STATIC_MESSAGE),
        intent=state["router"].intent if state.get("router") else "",
        sql=sql_result.sql if sql_result else "",
        rows=sql_result.rows if sql_result else [],
        interpretation=state.get("interpretation"),
        steps=state.get("steps", []),
    )
    record_io({"question": question}, {"status": result.status, "answer": result.answer, "sql": result.sql})
    return result


def run_pipeline(question: str) -> PipelineResult:
    """Run a question through all agents and return a structured result."""
    start = perf_counter()
    result = _run(question)
    result.duration_ms = round((perf_counter() - start) * 1000, 1)
    save_trace(result)
    return result
