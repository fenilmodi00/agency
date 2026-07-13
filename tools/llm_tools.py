"""CrewAI tools for calling Fireworks LLM with token tracking.

These tools wrap the low-level llm_client for use by CrewAI agents.
They do NOT replace the CrewAI agent LLM routing (get_fireworks_llm).
"""

from functools import wraps

import llm_client
from config import MAX_TOKENS_PER_AGENT, MODEL_OUTREACH
from loguru import logger

# Use CrewAI's @tool when available; fall back to a pass-through decorator
try:
    from crewai.tools import tool
except ImportError:
    def tool(fn):  # type: ignore[misc]
        @wraps(fn)
        def wrapper(*args, **kwargs):
            return fn(*args, **kwargs)

        wrapper.name = fn.__name__
        return wrapper


@tool
def call_fireworks_llm(
    prompt: str,
    model: str = None,
    temperature: float = 0.2,
    max_tokens: int = None,
) -> str:
    """Call Fireworks LLM with a single user prompt and return the text response.

    Logs token usage. Returns an error string on failure.
    """
    if max_tokens is None:
        max_tokens = MAX_TOKENS_PER_AGENT

    messages = [{"role": "user", "content": prompt}]

    try:
        content, usage = llm_client.call_fireworks_chat(
            messages=messages,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        logger.info(
            f"call_fireworks_llm: total_tokens={usage.get('total_tokens', 0)} "
            f"model={model or llm_client.MODEL_OUTREACH}"
        )
        return content
    except Exception as exc:
        logger.error(f"call_fireworks_llm failed: {exc}")
        return f"[LLM Error] {exc}"


@tool
def generate_gujarati_text(prompt: str) -> str:
    """Generate Gujarati text using the outreach model."""
    if hasattr(call_fireworks_llm, "run"):
        return call_fireworks_llm.run(prompt=prompt, model=MODEL_OUTREACH)
    return call_fireworks_llm(prompt=prompt, model=MODEL_OUTREACH)