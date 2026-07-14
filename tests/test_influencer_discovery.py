"""Tests for the Influencer Discovery agent — output shape and prompt loading."""

import json
from pathlib import Path
from unittest.mock import patch

import pytest

from agents._base import parse_prompt_sections
from agents.scout.influencer_discovery import (
    _load_influencer_discovery_prompt,
    get_influencer_discovery_agent,
    get_influencer_discovery_task,
)


class TestInfluencerDiscoveryPrompt:
    def testparse_prompt_sections(self):
        text = (
            "## Role\nYou are a discovery specialist.\n\n"
            "## Goal\nFind influencers.\n\n"
            "## Backstory\nDiscovery expert.\n"
        )
        sections = parse_prompt_sections(text)
        assert sections["Role"] == "You are a discovery specialist."
        assert sections["Goal"] == "Find influencers."
        assert sections["Backstory"] == "Discovery expert."

    def test_load_prompt_file_exists(self):
        path = (
            Path(__file__).resolve().parent.parent
            / "prompts" / "influencer_discovery_prompt.txt"
        )
        assert path.exists(), f"Prompt file not found: {path}"
        text = path.read_text(encoding="utf-8")
        sections = parse_prompt_sections(text)
        assert sections["Role"], "Role section should be non-empty"
        assert sections["Goal"], "Goal section should be non-empty"
        assert sections["Backstory"], "Backstory section should be non-empty"

    def test_load_prompt_from_module(self):
        sections = _load_influencer_discovery_prompt()
        assert "Role" in sections
        assert "Goal" in sections
        assert "Backstory" in sections


class TestInfluencerDiscoveryAgent:
    @patch("agents.scout.influencer_discovery.get_fireworks_llm")
    @patch("agents.scout.influencer_discovery.Agent")
    def test_get_agent_returns_agent(self, MockAgent, mock_llm):
        """get_influencer_discovery_agent should create an Agent instance."""
        instance = MockAgent.return_value
        result = get_influencer_discovery_agent()
        assert result is instance
        MockAgent.assert_called_once()

    @patch("agents.scout.influencer_discovery.get_fireworks_llm")
    @patch("agents.scout.influencer_discovery.Agent")
    @patch("agents.scout.influencer_discovery.Task")
    def test_get_task_returns_task(self, MockTask, MockAgent, mock_llm):
        """get_influencer_discovery_task should create a Task instance."""
        instance = MockTask.return_value
        agent = get_influencer_discovery_agent()
        task = get_influencer_discovery_task("test brief", agent)
        assert task is instance
        MockTask.assert_called_once()

    @patch("agents.scout.influencer_discovery.get_fireworks_llm")
    @patch("agents.scout.influencer_discovery.Agent")
    def test_agent_uses_correct_model(self, MockAgent, mock_llm):
        """Agent should be created with MODEL_SCOUT_DISCOVERY."""
        from config import MODEL_SCOUT_DISCOVERY

        get_influencer_discovery_agent()
        mock_llm.assert_called_once_with(MODEL_SCOUT_DISCOVERY)


class TestInfluencerDiscoveryOutputShape:
    def test_expected_output_keys(self):
        """Sample discovery output shape is valid."""
        output = {
            "search_criteria": {"niche": "sustainable fashion", "platforms": ["instagram"]},
            "candidate_pool_stats": {"total_screened": 43, "passed_filters": 15},
            "shortlist": [
                {
                    "tier": "must-reach",
                    "handle": "@sustainablestyle_sarah",
                    "preliminary_fit_score": 24,
                    "platform": "instagram",
                    "followers": 47000,
                    "engagement_rate": 5.2,
                }
            ],
            "recommendations": {"next_step": "pass to fit-scorer for STAR scoring"},
        }
        assert "search_criteria" in output
        assert "shortlist" in output
        assert "recommendations" in output
        assert len(output["shortlist"]) >= 1
        assert "tier" in output["shortlist"][0]

    def test_output_json_serializable(self):
        output = {"shortlist": [{"handle": "@test", "tier": "must-reach"}]}
        assert json.loads(json.dumps(output)) == output
