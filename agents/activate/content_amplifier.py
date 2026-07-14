"""Activate content amplifier — paid amplification and repurpose strategies."""

from pathlib import Path

from config import MODEL_ACTIVATE_AMPLIFIER
from llm_client import get_fireworks_llm
from tools.connectors.tavily_tools import tavily_search
from tools.connectors.firecrawl_tools import firecrawl_scrape

try:
    from crewai import Agent, Task
except ImportError:
    class Agent:  # type: ignore[no-redef]
        def __init__(self, **kwargs):
            self.__dict__.update(kwargs)

    class Task:  # type: ignore[no-redef]
        def __init__(self, **kwargs):
            self.__dict__.update(kwargs)


_PROMPT_SECTIONS = ("Role", "Goal", "Backstory")


def _parse_prompt_sections(text: str) -> dict:
    """Return a dict mapping section name to content for ## Role/Goal/Backstory."""
    sections = {name: "" for name in _PROMPT_SECTIONS}
    current = None
    lines = []

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


def _load_content_amplifier_prompt() -> dict:
    path = (
        Path(__file__).resolve().parent.parent.parent
        / "prompts" / "content_amplifier_prompt.txt"
    )
    text = path.read_text(encoding="utf-8")
    return _parse_prompt_sections(text)


AMPLIFIER_TASK_DESCRIPTION = """\
You are creating a content amplification strategy for approved creator content.

## Input
You will receive:
- content_set: JSON array of approved creator content pieces
- brief_context: the campaign brief
- budget: optional amplification budget
- mode: "paid" or "repurpose"

## Process

1. **Research the campaign topic.** Call `tavily_search(query="<campaign topic>")`
   to find current trends, audience conversations, and competitive context.

2. **Scrape relevant reference pages.** Use `firecrawl_scrape(url)` to pull details
   from any relevant URLs in the brief or content set.

3. **Build the strategy:**
   - **Paid mode:** Score each content piece /25 on organic performance, hook
     quality, message clarity, production quality, CTA. Tier into Must Amplify /
     Consider / Do Not Amplify. Allocate budget across tiers. Sum to stated budget.
   - **Repurpose mode:** Audit content inventory with rights levels. Map each
     source asset to 3+ output formats across 2+ channels. Build a 30-day
     distribution plan.

4. **Label every metric** as Measured, User-provided, or Estimated. Never invent
   reach, engagement, CPM, ROAS, or rights numbers.

## Output
Return a JSON object with:
{{
  "mode": "paid" | "repurpose",
  "content_scores": [
    {{
      "content_id": "<id>",
      "title": "<content title>",
      "score": <0-25>,
      "tier": "must_amplify" | "consider" | "do_not_amplify",
      "recommended_spend": <float or null>
    }}
  ],
  "strategy_summary": "<overview>",
  "budget_allocation": {{ "<content_id>": <float> }},
  "distribution_plan": "<30-day plan or null for paid>",
  "rights_summary": "<rights levels or null for paid>",
  "metric_labels": {{ "<metric>": "Measured" | "User-provided" | "Estimated" }}
}}

Return ONLY valid JSON. No markdown fences, no extra text.
"""


def get_content_amplifier_agent() -> "Agent":
    """Return a CrewAI Agent for the Activate-phase content amplifier."""
    prompt = _load_content_amplifier_prompt()

    return Agent(
        role=prompt.get("Role") or "Content Amplifier",
        goal=prompt.get("Goal") or (
            "Produce content amplification strategies — paid (boost/whitelist/dark posts) "
            "or repurpose (multi-channel asset reuse). Never score publishability."
        ),
        backstory=prompt.get("Backstory") or "",
        llm=get_fireworks_llm(MODEL_ACTIVATE_AMPLIFIER),
        tools=[tavily_search, firecrawl_scrape],
        verbose=True,
        allow_delegation=False,
    )


def get_content_amplifier_task(
    content_set: str,
    agent: "Agent",
    brief_context: str = "",
    budget: float = 0.0,
    mode: str = "paid",
) -> "Task":
    """Return a CrewAI Task for the content amplifier.

    Args:
        content_set: JSON string of approved content pieces.
        agent: The content amplifier agent.
        brief_context: Campaign brief context.
        budget: Amplification budget (0.0 for repurpose mode).
        mode: "paid" or "repurpose".
    """
    description = AMPLIFIER_TASK_DESCRIPTION
    description += f"\n\n## Content Set\n{content_set}"
    if brief_context:
        description += f"\n\n## Brief Context\n{brief_context}"
    description += f"\n\n## Budget\n{budget}"
    description += f"\n\n## Mode\n{mode}"

    return Task(
        description=description,
        expected_output=(
            "JSON object with: mode (paid/repurpose), content_scores (list), "
            "strategy_summary (string), budget_allocation (dict), "
            "distribution_plan (string or null), rights_summary (string or null), "
            "metric_labels (dict)."
        ),
        agent=agent,
    )
