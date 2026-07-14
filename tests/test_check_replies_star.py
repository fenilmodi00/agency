"""Verify that check_replies.py imports resolve from the enriched activate agents."""

import pytest


def test_negotiator_import_resolves():
    """get_outreach_manager_agent should be importable as get_negotiator_agent."""
    from agents.activate.outreach_manager import (
        get_outreach_manager_agent as get_negotiator_agent,
    )

    assert callable(get_negotiator_agent)


def test_contract_import_resolves():
    """get_contract_helper_agent should be importable as get_contract_agent."""
    from agents.activate.contract_helper import (
        get_contract_helper_agent as get_contract_agent,
    )

    assert callable(get_contract_agent)