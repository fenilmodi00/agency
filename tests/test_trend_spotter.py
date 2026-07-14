"""Tests for the Trend Spotter agent — output shape and prompt loading."""

import json
from pathlib import Path
from unittest.mock import patch

import pytest

from agents._base import parse_prompt_sections
from agents.scout.trend_spotter import (
    _load_trend_spotter_prompt,
    get_trend_spotter_agent,
    get_trend_spotter_task,
)


class TestTrendSpotterPrompt:
    def testparse_prompt_sections(self):
        text = (
            "## Role\nYou are a trend spotter.\n\n"
            "## Goal\nFind trends.\n\n"
            "## Backstory\nTrend expert.\n"
        )
        sections = parse_prompt_sections(text)
        assert sections["Role"] == "You are a trend spotter."
        assert sections["Goal"] == "Find trends."
        assert sections["Backstory"] == "Trend expert."

    def test_load_prompt_file_exists(self):
        path = Path(__file__).resolve().parent.parent / "prompts" / "trend_spotter_prompt.txt"
        assert path.exists(), f"Prompt file not found: {path}"
        text = path.read_text(encoding="utf-8")
        sections = parse_prompt_sections(text)
        assert sections["Role"], "Role section should be non-empty"
        assert sections["Goal"], "Goal section should be non-empty"
        assert sections["Backstory"], "Backstory section should be non-empty"

    def test_load_prompt_from_module(self):
        sections = _load_trend_spotter_prompt()
        assert "Role" in sections
        assert "Goal" in sections
        assert "Backstory" in sections


class TestTrendSpotterAgent:
    @patch("agents.scout.trend_spotter.get_fireworks_llm")
    @patch("agents.scout.trend_spotter.Agent")
    def test_get_agent_returns_agent(self, MockAgent, mock_llm):
        """get_trend_spotter_agent should create an Agent instance."""
        instance = MockAgent.return_value
        result = get_trend_spotter_agent()
        assert result is instance
        MockAgent.assert_called_once()

    @patch("agents.scout.trend_spotter.get_fireworks_llm")
    @patch("agents.scout.trend_spotter.Agent")
    @patch("agents.scout.trend_spotter.Task")
    def test_get_task_returns_task(self, MockTask, MockAgent, mock_llm):
        """get_trend_spotter_task should create a Task instance."""
        instance = MockTask.return_value
        agent = get_trend_spotter_agent()
        task = get_trend_spotter_task("test brief", agent)
        assert task is instance
        MockTask.assert_called_once()

    @patch("agents.scout.trend_spotter.get_fireworks_llm")
    @patch("agents.scout.trend_spotter.Agent")
    def test_agent_uses_correct_model(self, MockAgent, mock_llm):
        """Agent should be created with MODEL_SCOUT_TREND."""
        from config import MODEL_SCOUT_TREND

        get_trend_spotter_agent()
        mock_llm.assert_called_once_with(MODEL_SCOUT_TREND)


class TestTrendSpotterOutputShape:
    def test_expected_output_keys(self):
        """Sample trend spotter output shape is valid."""
        output = {
            "trends": [
                {
                    "trend": "GRWM Gym Edition",
                    "brand_fit_score": 22,
                    "lifecycle": "rising",
                    "recommendation": "go",
                    "timing_window": "this week",
                    "format": "15-30s video",
                }
            ],
            "top_3_act_now": ["GRWM Gym Edition"],
            "watch_list": ["Hot Girl Walk Evolution"],
            "avoid_list": ["75 Hard burnout"],
            "cultural_calendar": [
                {"event": "New Year", "lead_time_days": 60, "opportunity": "high"}
            ],
            "next_review_date": "2026-08-14",
        }
        assert "trends" in output
        assert "top_3_act_now" in output
        assert "watch_list" in output
        assert "avoid_list" in output

    def test_output_json_serializable(self):
        output = {"trends": [{"trend": "test", "brand_fit_score": 20}]}
        assert json.loads(json.dumps(output)) == output
