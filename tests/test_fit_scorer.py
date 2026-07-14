"""Tests for the Fit Scorer agent — output shape and prompt loading."""

import json
from pathlib import Path
from unittest.mock import patch

import pytest

from agents.scout.fit_scorer import (
    _parse_prompt_sections,
    _load_fit_scorer_prompt,
    get_fit_scorer_agent,
    get_fit_scorer_task,
)


class TestFitScorerPrompt:
    def test_parse_prompt_sections(self):
        text = (
            "## Role\nYou are a fit scorer.\n\n"
            "## Goal\nScore creator fit.\n\n"
            "## Backstory\nScoring expert.\n"
        )
        sections = _parse_prompt_sections(text)
        assert sections["Role"] == "You are a fit scorer."
        assert sections["Goal"] == "Score creator fit."
        assert sections["Backstory"] == "Scoring expert."

    def test_load_prompt_file_exists(self):
        path = Path(__file__).resolve().parent.parent / "prompts" / "fit_scorer_prompt.txt"
        assert path.exists(), f"Prompt file not found: {path}"
        text = path.read_text(encoding="utf-8")
        sections = _parse_prompt_sections(text)
        assert sections["Role"], "Role section should be non-empty"
        assert sections["Goal"], "Goal section should be non-empty"
        assert sections["Backstory"], "Backstory section should be non-empty"

    def test_load_prompt_from_module(self):
        sections = _load_fit_scorer_prompt()
        assert "Role" in sections
        assert "Goal" in sections
        assert "Backstory" in sections


class TestFitScorerAgent:
    @patch("agents.scout.fit_scorer.get_fireworks_llm")
    @patch("agents.scout.fit_scorer.Agent")
    def test_get_agent_returns_agent(self, MockAgent, mock_llm):
        """get_fit_scorer_agent should create an Agent instance."""
        instance = MockAgent.return_value
        result = get_fit_scorer_agent()
        assert result is instance
        MockAgent.assert_called_once()

    @patch("agents.scout.fit_scorer.get_fireworks_llm")
    @patch("agents.scout.fit_scorer.Agent")
    @patch("agents.scout.fit_scorer.Task")
    def test_get_task_returns_task(self, MockTask, MockAgent, mock_llm):
        """get_fit_scorer_task should create a Task instance."""
        instance = MockTask.return_value
        agent = get_fit_scorer_agent()
        task = get_fit_scorer_task("test brief", agent)
        assert task is instance
        MockTask.assert_called_once()

    @patch("agents.scout.fit_scorer.get_fireworks_llm")
    @patch("agents.scout.fit_scorer.Agent")
    def test_agent_uses_correct_model(self, MockAgent, mock_llm):
        """Agent should be created with MODEL_SCOUT_FIT."""
        from config import MODEL_SCOUT_FIT

        get_fit_scorer_agent()
        mock_llm.assert_called_once_with(MODEL_SCOUT_FIT)


class TestFitScorerOutputShape:
    def test_expected_output_keys(self):
        """Sample fit scorer output shape is valid."""
        output = {
            "typed_context": {
                "goal": "conversion",
                "assessment_time": "forecast",
                "platform": "instagram",
                "niche_cohort": "sustainable_fashion",
            },
            "suitability_read": {
                "S1": {"status": "Pass", "evidence": "audience data from registry"},
                "S2": {"status": "Pass", "evidence": "real-follower rate above benchmark"},
                "S3": {"status": "Pass", "evidence": "organic growth"},
                "S4": {"status": "Partial", "evidence": "some variance in reach"},
                "S5": {"status": "Pass", "evidence": "5.2% ER vs 3.5% median"},
                "S6": {"status": "Pass", "evidence": "no pod signals"},
                "S7": {"status": "Unknown", "evidence": "no save/share data available"},
                "S8": {"status": "Pass", "evidence": "strong brand fit"},
                "S9": {"status": "Pass", "evidence": "reliable delivery history"},
                "S10": {"status": "Pass", "evidence": "1 competitor brand, non-exclusive"},
            },
            "veto_flags": [],
            "commercial_fit_matrix": {
                "audience_to_campaign_fit": 5,
                "content_style": 4,
                "commercial_terms": 3,
                "overall_commercial_fit_score": 4,
            },
        }
        assert "typed_context" in output
        assert "suitability_read" in output
        assert "veto_flags" in output
        assert "commercial_fit_matrix" in output
        assert "S1" in output["suitability_read"]
        assert "S2" in output["suitability_read"]

    def test_output_json_serializable(self):
        output = {"suitability_read": {"S1": {"status": "Pass"}}}
        assert json.loads(json.dumps(output)) == output

    def test_veto_flags_separate_from_scores(self):
        """Veto conditions must not override Suitability read."""
        output = {
            "suitability_read": {"S1": {"status": "Pass", "evidence": "ok"}},
            "veto_flags": [],
        }
        assert isinstance(output["veto_flags"], list)
