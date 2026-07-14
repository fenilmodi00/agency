"""Tests for the Audience Mapper agent — output shape and prompt loading."""

import json
from pathlib import Path
from unittest.mock import patch

import pytest

from agents.scout.audience_mapper import (
    _parse_prompt_sections,
    _load_audience_mapper_prompt,
    get_audience_mapper_agent,
    get_audience_mapper_task,
)


class TestAudienceMapperPrompt:
    def test_parse_prompt_sections(self):
        text = (
            "## Role\nYou are a test role.\n\n"
            "## Goal\nYou have a test goal.\n\n"
            "## Backstory\nThis is a test backstory.\n"
        )
        sections = _parse_prompt_sections(text)
        assert sections["Role"] == "You are a test role."
        assert sections["Goal"] == "You have a test goal."
        assert sections["Backstory"] == "This is a test backstory."

    def test_load_prompt_file_exists(self):
        path = Path(__file__).resolve().parent.parent / "prompts" / "audience_mapper_prompt.txt"
        assert path.exists(), f"Prompt file not found: {path}"
        text = path.read_text(encoding="utf-8")
        sections = _parse_prompt_sections(text)
        assert sections["Role"], "Role section should be non-empty"
        assert sections["Goal"], "Goal section should be non-empty"
        assert sections["Backstory"], "Backstory section should be non-empty"

    def test_load_prompt_from_module(self):
        sections = _load_audience_mapper_prompt()
        assert "Role" in sections
        assert "Goal" in sections
        assert "Backstory" in sections


class TestAudienceMapperAgent:
    @patch("agents.scout.audience_mapper.get_fireworks_llm")
    @patch("agents.scout.audience_mapper.Agent")
    def test_get_agent_returns_agent(self, MockAgent, mock_llm):
        """get_audience_mapper_agent should create an Agent instance."""
        instance = MockAgent.return_value
        result = get_audience_mapper_agent()
        assert result is instance
        MockAgent.assert_called_once()

    @patch("agents.scout.audience_mapper.get_fireworks_llm")
    @patch("agents.scout.audience_mapper.Agent")
    @patch("agents.scout.audience_mapper.Task")
    def test_get_task_returns_task(self, MockTask, MockAgent, mock_llm):
        """get_audience_mapper_task should create a Task instance."""
        instance = MockTask.return_value
        agent = get_audience_mapper_agent()
        task = get_audience_mapper_task("test brief", agent)
        assert task is instance
        MockTask.assert_called_once()

    @patch("agents.scout.audience_mapper.get_fireworks_llm")
    @patch("agents.scout.audience_mapper.Agent")
    def test_agent_uses_correct_model(self, MockAgent, mock_llm):
        """Agent should be created with MODEL_SCOUT_AUDIENCE."""
        from config import MODEL_SCOUT_AUDIENCE

        get_audience_mapper_agent()
        mock_llm.assert_called_once_with(MODEL_SCOUT_AUDIENCE)


class TestAudienceMapperOutputShape:
    def test_expected_output_keys(self):
        """Sample audience mapper output shape is valid."""
        output = {
            "mode": "audience",
            "demographics": {"age_range": "18-35", "confidence": "High"},
            "psychographics": {"values": ["authenticity", "value"], "confidence": "Med"},
            "platform_priorities": [
                {"platform": "instagram", "priority": 1},
            ],
            "personas": [
                {"name": "Priya", "bio": "Health-conscious millennial"},
            ],
            "selection_criteria": {
                "must_have": ["language: gu", "niche: food"],
                "nice_to_have": ["engagement > 3%"],
                "red_flags": ["fake followers"],
            },
        }
        assert "mode" in output
        assert "demographics" in output
        assert "personas" in output
        assert "selection_criteria" in output

    def test_output_json_serializable(self):
        output = {"mode": "audience", "demographics": {"age_range": "18-35"}}
        assert json.loads(json.dumps(output)) == output
