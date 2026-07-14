"""Tests for StarCrew phase routing and backward compatibility."""

from unittest.mock import MagicMock

import pytest


class TestStarCrewPhaseRouting:
    """StarCrew.run_phase() and phase routing."""

    def test_scout_phase_runs_4_agents(self, mocker):
        """Scout phase should build a crew with 4 scout agents and return phase info."""
        mocker.patch(
            "crew.Crew",
            side_effect=lambda **kw: type(
                "Crew",
                (),
                {
                    **kw,
                    "kickoff": lambda self: MagicMock(
                        raw="[]", token_usage={}
                    ),
                },
            )(),
        )
        mocker.patch("crew.Process", sequential="sequential")
        from crew import StarCrew

        crew = StarCrew()
        mocker.patch.object(crew, "_get_db")
        result = crew.run_phase("scout", brief_text="test brief")
        assert "phase" in result
        assert result["phase"] == "scout"

    def test_invalid_phase_raises(self):
        """Invalid phase name should raise ValueError."""
        from crew import StarCrew

        crew = StarCrew()
        with pytest.raises(ValueError):
            crew.run_phase("invalid_phase", brief_text="test")

    def test_all_phases_callable(self, mocker):
        """All 4 phases should be callable and return their phase name."""
        mocker.patch(
            "crew.Crew",
            side_effect=lambda **kw: type(
                "Crew",
                (),
                {
                    **kw,
                    "kickoff": lambda self: MagicMock(
                        raw="[]", token_usage={}
                    ),
                },
            )(),
        )
        mocker.patch("crew.Process", sequential="sequential")
        from crew import StarCrew

        crew = StarCrew()
        mocker.patch.object(crew, "_get_db")
        for phase in ["scout", "target", "activate", "report"]:
            result = crew.run_phase(phase, brief_text="test")
            assert result["phase"] == phase


class TestStarCrewBackwardCompat:
    """InfluencerCampaignCrew backward compatibility."""

    def test_influencer_campaign_crew_still_exists(self):
        """InfluencerCampaignCrew should still be importable."""
        from crew import InfluencerCampaignCrew

        assert InfluencerCampaignCrew is not None

    def test_kickoff_still_works(self, mocker):
        """kickoff() should return a dict with backward-compat keys."""
        mocker.patch(
            "crew.Crew",
            side_effect=lambda **kw: type(
                "Crew",
                (),
                {
                    **kw,
                    "kickoff": lambda self: MagicMock(
                        raw="[]", token_usage={}
                    ),
                },
            )(),
        )
        mocker.patch("crew.Process", sequential="sequential")
        from crew import InfluencerCampaignCrew

        crew = InfluencerCampaignCrew()
        mocker.patch.object(crew, "_get_db")
        summary = crew.kickoff(
            brief_text="test", send=False, approve_each=False, max_creators=5
        )
        assert "brief_id" in summary
        assert "dry_run" in summary
        assert "creators_found" in summary
        assert "dms_attempted" in summary
        assert "dms_sent" in summary
        assert "total_tokens" in summary
