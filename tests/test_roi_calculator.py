# tests/test_roi_calculator.py
"""Tests for the ROI Calculator agent (Report phase)."""

from unittest.mock import MagicMock

import pytest


class TestRoiCalculatorAgent:
    def test_factory_returns_agent(self, mocker):
        mocker.patch("agents.report.roi_calculator.get_fireworks_llm", return_value=MagicMock())
        mocker.patch("agents.report.roi_calculator.Agent", side_effect=lambda **kw: type("Agent", (), kw)())
        from agents.report.roi_calculator import get_roi_calculator_agent
        agent = get_roi_calculator_agent()
        assert agent is not None
        assert hasattr(agent, "role")
        assert hasattr(agent, "goal")
        assert hasattr(agent, "tools")
        assert agent.verbose is True
        assert agent.allow_delegation is False

    def test_factory_calls_get_fireworks_llm(self, mocker):
        mock_get_llm = mocker.patch("agents.report.roi_calculator.get_fireworks_llm", return_value=MagicMock())
        mocker.patch("agents.report.roi_calculator.Agent.__init__", return_value=None)
        from agents.report.roi_calculator import get_roi_calculator_agent
        get_roi_calculator_agent()
        assert mock_get_llm.call_count >= 1

    def test_task_has_expected_output(self, mocker):
        mocker.patch("agents.report.roi_calculator.get_fireworks_llm", return_value=MagicMock())
        mocker.patch("agents.report.roi_calculator.Agent", side_effect=lambda **kw: type("Agent", (), kw)())
        mocker.patch("agents.report.roi_calculator.Task", side_effect=lambda **kw: type("Task", (), kw)())
        from agents.report.roi_calculator import get_roi_calculator_agent, get_roi_calculator_task
        agent = get_roi_calculator_agent()
        task = get_roi_calculator_task('{"spend": 25000, "revenue": 72000}', agent)
        assert hasattr(task, "expected_output")
        assert isinstance(task.expected_output, str)
        assert len(task.expected_output) > 10
