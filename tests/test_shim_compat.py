"""Tests that old agent imports still work through thin shims."""


def test_discovery_shim_exports():
    from agents.discovery import get_discovery_agent, get_discovery_task
    assert callable(get_discovery_agent)
    assert callable(get_discovery_task)


def test_proposal_shim_exports():
    from agents.proposal import get_proposal_agent, get_proposal_task
    assert callable(get_proposal_agent)
    assert callable(get_proposal_task)


def test_outreach_shim_exports():
    from agents.outreach import get_outreach_agent, get_outreach_task
    assert callable(get_outreach_agent)
    assert callable(get_outreach_task)


def test_negotiator_shim_exports():
    from agents.negotiator import get_negotiator_agent
    assert callable(get_negotiator_agent)


def test_contract_shim_exports():
    from agents.contract import get_contract_agent
    assert callable(get_contract_agent)