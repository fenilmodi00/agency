"""Shared utilities for agent modules.

Centralizes:
- CrewAI Agent/Task import stubs (so submodules don't repeat the try/except)
- CrewAI @tool import with fallback decorator
- Prompt section parsing (## Role / ## Goal / ## Backstory)

Every agent submodule should import from here instead of duplicating
these definitions.
"""

from functools import wraps
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# CrewAI import stubs — modules must remain importable without crewai installed.
# ---------------------------------------------------------------------------

try:
    from crewai import Agent, Task
except ImportError:
    class Agent:  # type: ignore[no-redef]
        def __init__(self, **kwargs: Any) -> None:
            self.__dict__.update(kwargs)

    class Task:  # type: ignore[no-redef]
        def __init__(self, **kwargs: Any) -> None:
            self.__dict__.update(kwargs)

try:
    from crewai.tools import tool
except ImportError:
    def tool(fn):  # type: ignore[misc]
        @wraps(fn)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            return fn(*args, **kwargs)
        wrapper.name = fn.__name__
        return wrapper


# ---------------------------------------------------------------------------
# Prompt parsing — extracts ## Role / ## Goal / ## Backstory sections from
# a markdown prompt file.
# ---------------------------------------------------------------------------

_PROMPT_SECTIONS = ("Role", "Goal", "Backstory")


def parse_prompt_sections(text: str) -> dict:
    """Return a dict mapping section name to content for ## Role/Goal/Backstory.

    Args:
        text: The full text of a prompt file containing ## Role, ## Goal,
              and ## Backstory markdown sections.

    Returns:
        Dict with keys "Role", "Goal", "Backstory" mapping to section content.
        Missing sections are empty strings.
    """
    sections: dict[str, str] = {name: "" for name in _PROMPT_SECTIONS}
    current: str | None = None
    lines: list[str] = []

    for line in text.splitlines():
        header = line.strip().removeprefix("## ").removeprefix("# ")
        if header in _PROMPT_SECTIONS:
            if current is not None:
                sections[current] = "\n".join(lines).strip()
                lines = []
            current = header
        elif current is not None:
            lines.append(line)

    if current is not None:
        sections[current] = "\n".join(lines).strip()

    return sections


def load_prompt(prompts_dir: Path, filename: str) -> dict:
    """Load and parse a prompt file from the prompts directory.

    Args:
        prompts_dir: Path to the prompts/ directory.
        filename: Name of the prompt file (e.g. "discovery_prompt.txt").

    Returns:
        Dict with parsed Role/Goal/Backstory sections.
    """
    path = Path(prompts_dir) / filename
    text = path.read_text(encoding="utf-8")
    return parse_prompt_sections(text)
