"""Thin shim — re-exports from agents.target.campaign_planner for backward compat."""

from agents.target.campaign_planner import (
    get_campaign_planner_agent as get_proposal_agent,
    get_campaign_planner_task as get_proposal_task,
)

__all__ = ["get_proposal_agent", "get_proposal_task"]