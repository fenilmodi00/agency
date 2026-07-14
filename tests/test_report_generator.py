# tests/test_report_generator.py
"""Tests for the Report Generator agent (Report phase)."""

from unittest.mock import MagicMock

import pytest


class TestReportGeneratorAgent:
    def test_factory_returns_agent(self, mocker):
        mocker.patch("agents.report.report_generator.get_fireworks_llm", return_value=MagicMock())
        mocker.patch("agents.report.report_generator.Agent", side_effect=lambda **kw: type("Agent", (), kw)())
        from agents.report.report_generator import get_report_generator_agent
        agent = get_report_generator_agent()
        assert agent is not None
        assert hasattr(agent, "role")
        assert hasattr(agent, "goal")
        assert hasattr(agent, "tools")
        assert agent.verbose is True
        assert agent.allow_delegation is False

    def test_factory_calls_get_fireworks_llm(self, mocker):
        mock_get_llm = mocker.patch("agents.report.report_generator.get_fireworks_llm", return_value=MagicMock())
        mocker.patch("agents.report.report_generator.Agent.__init__", return_value=None)
        from agents.report.report_generator import get_report_generator_agent
        get_report_generator_agent()
        assert mock_get_llm.call_count >= 1

    def test_task_has_expected_output(self, mocker):
        mocker.patch("agents.report.report_generator.get_fireworks_llm", return_value=MagicMock())
        mocker.patch("agents.report.report_generator.Agent", side_effect=lambda **kw: type("Agent", (), kw)())
        mocker.patch("agents.report.report_generator.Task", side_effect=lambda **kw: type("Task", (), kw)())
        from agents.report.report_generator import get_report_generator_agent, get_report_generator_task
        agent = get_report_generator_agent()
        task = get_report_generator_task("test campaign", "executive", agent)
        assert hasattr(task, "expected_output")
        assert isinstance(task.expected_output, str)
        assert len(task.expected_output) > 10
