"""Thin shim — re-exports from agents.scout.influencer_discovery for backward compat.

The enriched Discovery agent now lives at agents/scout/influencer_discovery.py.
This file preserves the existing import path: from agents.discovery import get_discovery_agent.
"""

from agents.scout.influencer_discovery import (
    get_influencer_discovery_agent as get_discovery_agent,
    get_influencer_discovery_task as get_discovery_task,
)

__all__ = ["get_discovery_agent", "get_discovery_task"]