"""Thin shim — re-exports from agents.activate.outreach_manager for backward compat."""

from agents.activate.outreach_manager import (
    get_outreach_manager_agent as get_outreach_agent,
    get_outreach_manager_task as get_outreach_task,
)

__all__ = ["get_outreach_agent", "get_outreach_task"]