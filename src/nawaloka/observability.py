import functools
import os
from contextvars import ContextVar, Token
from functools import lru_cache
from typing import Any, Callable

from langchain_core.callbacks import BaseCallbackHandler
from loguru import logger

from nawaloka.config import OBSERVABILITY_ENABLED

_usage: ContextVar[dict[str, int] | None] = ContextVar("usage", default=None)


class UsageCallback(BaseCallbackHandler):
    """Adds token counts from each LLM call to the active usage counter."""

    run_inline = True

    def on_llm_end(self, response, **kwargs: Any) -> None:
        usage = _usage.get()
        if usage is None:
            return
        for generations in response.generations:
            for generation in generations:
                meta = getattr(getattr(generation, "message", None), "usage_metadata", None) or {}
                usage["input"] += meta.get("input_tokens", 0)
                usage["output"] += meta.get("output_tokens", 0)


def start_usage() -> Token:
    """Begin counting tokens for the current agent step."""
    return _usage.set({"input": 0, "output": 0})


def stop_usage(token: Token) -> dict[str, int]:
    """Stop counting and return the totals for the step."""
    usage = _usage.get() or {"input": 0, "output": 0}
    _usage.reset(token)
    return usage


@lru_cache(maxsize=1)
def get_langfuse():
    """Return the LangFuse client, or None if tracing is off or keys are missing."""
    if not OBSERVABILITY_ENABLED:
        return None
    secret = os.getenv("LANGFUSE_SECRET_KEY")
    public = os.getenv("LANGFUSE_PUBLIC_KEY")
    if not secret or not public:
        logger.warning("LangFuse keys not set, remote tracing is disabled")
        return None
    try:
        from langfuse import Langfuse

        return Langfuse(
            public_key=public,
            secret_key=secret,
            base_url=os.getenv("LANGFUSE_BASE_URL", "https://us.cloud.langfuse.com"),
        )
    except Exception as exc:
        logger.error("Could not start LangFuse: {}", exc)
        return None


def get_callbacks() -> list[BaseCallbackHandler]:
    """Callbacks attached to every LLM: local token counting plus LangFuse when enabled."""
    callbacks: list[BaseCallbackHandler] = [UsageCallback()]
    if get_langfuse() is not None:
        from langfuse.langchain import CallbackHandler

        callbacks.append(CallbackHandler())
    return callbacks


def observed(name: str) -> Callable:
    """Decorator that traces a function as a LangFuse observation when tracing is on."""

    def decorator(fn: Callable) -> Callable:
        wrapped = None

        @functools.wraps(fn)
        def inner(*args: Any, **kwargs: Any):
            nonlocal wrapped
            if get_langfuse() is None:
                return fn(*args, **kwargs)
            if wrapped is None:
                from langfuse import observe

                wrapped = observe(name=name, capture_input=False, capture_output=False)(fn)
            return wrapped(*args, **kwargs)

        return inner

    return decorator


def record_io(input: Any, output: Any) -> None:
    """Attach input and output to the current LangFuse observation."""
    client = get_langfuse()
    if client is None:
        return
    try:
        client.update_current_span(input=input, output=output)
    except Exception as exc:
        logger.debug("Could not record trace IO: {}", exc)


def flush() -> None:
    """Send any buffered events to LangFuse."""
    client = get_langfuse()
    if client is not None:
        client.flush()
