"""Thin shim — re-exports from agents.activate.outreach_manager for backward compat.

The Negotiator role is the outreach_manager agent in negotiation mode.
"""

from agents.activate.outreach_manager import get_outreach_manager_agent as get_negotiator_agent

__all__ = ["get_negotiator_agent"]