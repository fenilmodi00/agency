# tests/test_performance_analyzer.py
"""Tests for the Performance Analyzer agent (Report phase)."""

from unittest.mock import MagicMock

import pytest


class TestPerformanceAnalyzerAgent:
    def test_factory_returns_agent(self, mocker):
        mocker.patch("agents.report.performance_analyzer.get_fireworks_llm", return_value=MagicMock())
        mocker.patch("agents.report.performance_analyzer.Agent", side_effect=lambda **kw: type("Agent", (), kw)())
        from agents.report.performance_analyzer import get_performance_analyzer_agent
        agent = get_performance_analyzer_agent()
        assert agent is not None
        assert hasattr(agent, "role")
        assert hasattr(agent, "goal")
        assert hasattr(agent, "tools")
        assert agent.verbose is True
        assert agent.allow_delegation is False

    def test_factory_calls_get_fireworks_llm(self, mocker):
        mock_get_llm = mocker.patch("agents.report.performance_analyzer.get_fireworks_llm", return_value=MagicMock())
        mocker.patch("agents.report.performance_analyzer.Agent.__init__", return_value=None)
        from agents.report.performance_analyzer import get_performance_analyzer_agent
        get_performance_analyzer_agent()
        assert mock_get_llm.call_count >= 1

    def test_task_has_expected_output(self, mocker):
        mocker.patch("agents.report.performance_analyzer.get_fireworks_llm", return_value=MagicMock())
        mocker.patch("agents.report.performance_analyzer.Agent", side_effect=lambda **kw: type("Agent", (), kw)())
        mocker.patch("agents.report.performance_analyzer.Task", side_effect=lambda **kw: type("Task", (), kw)())
        from agents.report.performance_analyzer import get_performance_analyzer_agent, get_performance_analyzer_task
        agent = get_performance_analyzer_agent()
        task = get_performance_analyzer_task("test campaign", agent)
        assert hasattr(task, "expected_output")
        assert isinstance(task.expected_output, str)
        assert len(task.expected_output) > 10
