"""Thin shim — re-exports from agents.activate.contract_helper for backward compat."""

from agents.activate.contract_helper import get_contract_helper_agent as get_contract_agent

__all__ = ["get_contract_agent"]