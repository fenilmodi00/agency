"""LLM client utilities for Fireworks AI via OpenAI SDK and CrewAI."""

from openai import OpenAI
from crewai import LLM
from config import FIREWORKS_API_KEY, FIREWORKS_BASE_URL, MODEL_OUTREACH


def format_model_path(alias: str) -> str:
    """Map friendly aliases to real Fireworks model paths."""
    mapping = {
        "glm-5.2": "accounts/fireworks/models/glm-5p2",
        "qwen3.7-plus": "accounts/fireworks/models/qwen3p7-plus",
        "deepseek-v4-pro": "accounts/fireworks/models/deepseek-v4-pro",
    }
    return mapping.get(alias, alias)


def get_fireworks_llm(model_name: str) -> LLM:
    """Return a CrewAI LLM configured for Fireworks."""
    return LLM(
        model=model_name,
        api_key=FIREWORKS_API_KEY,
        base_url=FIREWORKS_BASE_URL,
        provider="openai",
    )


def get_token_usage(response) -> dict:
    """Extract token usage from an OpenAI-style response."""
    usage = getattr(response, "usage", None)
    if usage:
        return {
            "prompt_tokens": getattr(usage, "prompt_tokens", 0),
            "completion_tokens": getattr(usage, "completion_tokens", 0),
            "total_tokens": getattr(usage, "total_tokens", 0),
        }
    return {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}


def call_fireworks_chat(messages: list, model: str = None, temperature: float = 0.2, max_tokens: int = None) -> tuple[str, dict]:
    """Direct OpenAI SDK call to Fireworks. Returns (content, usage_dict)."""
    client = OpenAI(api_key=FIREWORKS_API_KEY, base_url=FIREWORKS_BASE_URL)
    model = model or MODEL_OUTREACH
    response = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
    )
    content = response.choices[0].message.content
    return content, get_token_usage(response)