"""Tests for the Narrative Registry protocol agent."""

from unittest.mock import patch

import pytest

from agents.protocol.narrative_registry import get_narrative_registry_agent


class TestNarrativeRegistryAgentFactory:
    """Agent factory returns an Agent with the expected configuration."""

    @patch("agents.protocol.narrative_registry.get_fireworks_llm")
    @patch("agents.protocol.narrative_registry.Agent")
    def test_factory_returns_agent(self, MockAgent, mock_llm):
        """get_narrative_registry_agent should create an Agent instance."""
        instance = MockAgent.return_value
        result = get_narrative_registry_agent()
        assert result is instance
        MockAgent.assert_called_once()

    @patch("agents.protocol.narrative_registry.get_fireworks_llm")
    @patch("agents.protocol.narrative_registry.Agent")
    def test_agent_uses_protocol_model(self, MockAgent, mock_llm):
        """Agent should be created with MODEL_PROTOCOL_REGISTRY model."""
        from config import MODEL_PROTOCOL_REGISTRY

        get_narrative_registry_agent()
        call_kwargs = MockAgent.call_args.kwargs
        assert call_kwargs["llm"] is mock_llm.return_value
        mock_llm.assert_called_once_with(MODEL_PROTOCOL_REGISTRY)

    @patch("agents.protocol.narrative_registry.get_fireworks_llm")
    @patch("agents.protocol.narrative_registry.Agent")
    def test_agent_tools_includes_registry_tools(self, MockAgent, mock_llm):
        """Agent should have registry_get, registry_propose, registry_verify."""
        from tools.registry_tools import registry_get, registry_propose, registry_verify

        get_narrative_registry_agent()
        call_kwargs = MockAgent.call_args.kwargs
        tools = call_kwargs["tools"]
        assert registry_get in tools
        assert registry_propose in tools
        assert registry_verify in tools

    @patch("agents.protocol.narrative_registry.get_fireworks_llm")
    @patch("agents.protocol.narrative_registry.Agent")
    def test_agent_verbose_and_no_delegation(self, MockAgent, mock_llm):
        """Agent should have verbose=True and allow_delegation=False."""
        get_narrative_registry_agent()
        call_kwargs = MockAgent.call_args.kwargs
        assert call_kwargs["verbose"] is True
        assert call_kwargs["allow_delegation"] is False
