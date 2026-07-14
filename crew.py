"""Sequential crew orchestration for the vernacular-creator-agents pipeline.

Discovery → Proposal → Outreach (no Negotiator / Contract).
"""

import json
from typing import Optional

from config import AGENTS_DB_PATH, MAX_TOTAL_TOKENS_PER_RUN
from database import Database
from llm_client import get_token_usage
from loguru import logger

try:
    from crewai import Crew, Process
except ImportError:
    # Minimal stubs so the module imports without crewai installed.
    class Process:  # type: ignore[no-redef]
        sequential = "sequential"

    class Crew:  # type: ignore[no-redef]
        def __init__(self, **kwargs):
            self.__dict__.update(kwargs)

        def kickoff(self, **kwargs):
            return MockCrewOutput()

    class MockCrewOutput:
        def __init__(self):
            self.raw = "[]"
            self.token_usage = {"total_tokens": 0, "prompt_tokens": 0, "completion_tokens": 0}

        def json(self):
            return self.raw


class StarCrew:
    """Orchestrates the 24-agent STAR pipeline with phase routing.

    Phases: scout → target → activate → report.
    Protocol agents are utility agents called within phases, not pipeline stages.
    """

    PHASES = ("scout", "target", "activate", "report")

    def __init__(self):
        self._db: Optional[Database] = None
        self._total_tokens: int = 0
        self._phase_results: dict[str, dict] = {}
        try:
            self._crew: Crew = Crew(agents=[], tasks=[], process=Process.sequential, verbose=False)
        except Exception:
            self._crew = type("Crew", (), {"kickoff": lambda self, **kw: None})()

    @property
    def crew(self) -> Optional[Crew]:
        """Return the most recently built Crew instance (after kickoff) or None."""
        return self._crew

    @crew.setter
    def crew(self, value: Crew) -> None:
        self._crew = value

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _get_db(self) -> Database:
        if self._db is None:
            self._db = Database(AGENTS_DB_PATH)
            self._db.init_db()
        return self._db

    def _track_tokens(self, usage: dict) -> None:
        """Accumulate total tokens and warn if budget exceeded."""
        added = usage.get("total_tokens", 0) if isinstance(usage, dict) else 0
        self._total_tokens += added
        if self._total_tokens > MAX_TOTAL_TOKENS_PER_RUN:
            logger.warning(
                "Token budget exceeded: %d / %d",
                self._total_tokens,
                MAX_TOTAL_TOKENS_PER_RUN,
            )

    @staticmethod
    def _safe_json_parse(text: str) -> list:
        """Best-effort JSON array parse from agent output."""
        text = text.strip()
        # Strip markdown fences if present
        if text.startswith("```"):
            text = text.split("\n", 1)[-1].rsplit("```", 1)[0].strip()
        try:
            data = json.loads(text)
            if isinstance(data, list):
                return data
        except json.JSONDecodeError:
            pass
        return []

    # ------------------------------------------------------------------
    # Phase routing
    # ------------------------------------------------------------------

    def run_phase(self, phase: str, brief_text: str, **kwargs) -> dict:
        """Run a single STAR phase. Returns a phase result dict."""
        if phase not in self.PHASES:
            raise ValueError(f"Invalid phase '{phase}'. Must be one of: {self.PHASES}")

        db = self._get_db()
        self._total_tokens = 0

        # Insert brief if this is the first phase
        brief_id = kwargs.get("brief_id")
        if brief_id is None:
            try:
                brief_id = db.insert_brief(raw_brief=brief_text)
            except Exception as exc:
                logger.error("Failed to insert brand brief: %s", exc)
                brief_id = None

        phase_method = getattr(self, f"_run_{phase}_phase")
        result = phase_method(brief_text, brief_id, **kwargs)
        result["phase"] = phase
        result["brief_id"] = brief_id
        result["total_tokens"] = self._total_tokens
        self._phase_results[phase] = result
        return result

    def run_all(
        self,
        brief_text: str,
        send: bool = False,
        approve_each: bool = False,
        max_creators: int = 10,
    ) -> dict:
        """Run all 4 STAR phases sequentially. Returns a combined summary."""
        db = self._get_db()
        self._total_tokens = 0
        self._phase_results = {}

        try:
            brief_id = db.insert_brief(raw_brief=brief_text)
        except Exception as exc:
            logger.error("Failed to insert brand brief: %s", exc)
            brief_id = None

        scout_result = self._run_scout_phase(brief_text, brief_id)
        target_result = self._run_target_phase(
            brief_text, brief_id, scout_result=scout_result
        )
        activate_result = self._run_activate_phase(
            brief_text,
            brief_id,
            target_result=target_result,
            send=send,
            approve_each=approve_each,
        )
        report_result = self._run_report_phase(
            brief_text, brief_id, activate_result=activate_result
        )

        return {
            "brief_id": brief_id,
            "scout": scout_result,
            "target": target_result,
            "activate": activate_result,
            "report": report_result,
            "total_tokens": self._total_tokens,
            "dry_run": not send,
        }

    # ------------------------------------------------------------------
    # Scout phase
    # ------------------------------------------------------------------

    def _run_scout_phase(
        self, brief_text: str, brief_id: Optional[int], **kwargs
    ) -> dict:
        """Run Scout: audience_mapper → trend_spotter → influencer_discovery → fit_scorer."""
        creators_found = 0
        try:
            from agents.scout.audience_mapper import (
                get_audience_mapper_agent,
                get_audience_mapper_task,
            )
            from agents.scout.trend_spotter import (
                get_trend_spotter_agent,
                get_trend_spotter_task,
            )
            from agents.scout.influencer_discovery import (
                get_influencer_discovery_agent,
                get_influencer_discovery_task,
            )
            from agents.scout.fit_scorer import (
                get_fit_scorer_agent,
                get_fit_scorer_task,
            )

            for get_agent, get_task, name in [
                (get_audience_mapper_agent, get_audience_mapper_task, "audience_mapper"),
                (get_trend_spotter_agent, get_trend_spotter_task, "trend_spotter"),
                (get_influencer_discovery_agent, get_influencer_discovery_task, "influencer_discovery"),
                (get_fit_scorer_agent, get_fit_scorer_task, "fit_scorer"),
            ]:
                agent = get_agent()
                task = get_task(brief_text, agent)
                self.crew = Crew(
                    agents=[agent],
                    tasks=[task],
                    process=Process.sequential,
                    verbose=True,
                )
                result = self.crew.kickoff()
                self._track_tokens(getattr(result, "token_usage", {}) or {})
                if name == "influencer_discovery":
                    ranked = self._safe_json_parse(getattr(result, "raw", "[]"))
                    creators_found = len(ranked)
                    self._phase_results["scout_creators"] = ranked

        except Exception as exc:
            logger.error("Scout phase failed: %s", exc)

        return {"creators_found": creators_found}

    # ------------------------------------------------------------------
    # Target phase
    # ------------------------------------------------------------------

    def _run_target_phase(
        self, brief_text: str, brief_id: Optional[int], **kwargs
    ) -> dict:
        """Run Target: competitor_tracker → campaign_planner → brief_generator → budget_optimizer."""
        proposals_generated = 0
        try:
            from agents.target.competitor_tracker import (
                get_competitor_tracker_agent,
                get_competitor_tracker_task,
            )
            from agents.target.campaign_planner import (
                get_campaign_planner_agent,
                get_campaign_planner_task,
            )
            from agents.target.brief_generator import (
                get_brief_generator_agent,
                get_brief_generator_task,
            )
            from agents.target.budget_optimizer import (
                get_budget_optimizer_agent,
                get_budget_optimizer_task,
            )

            for get_agent, get_task, name in [
                (get_competitor_tracker_agent, get_competitor_tracker_task, "competitor_tracker"),
                (get_campaign_planner_agent, get_campaign_planner_task, "campaign_planner"),
                (get_brief_generator_agent, get_brief_generator_task, "brief_generator"),
                (get_budget_optimizer_agent, get_budget_optimizer_task, "budget_optimizer"),
            ]:
                agent = get_agent()
                task = get_task(brief_text, agent)
                self.crew = Crew(
                    agents=[agent],
                    tasks=[task],
                    process=Process.sequential,
                    verbose=True,
                )
                result = self.crew.kickoff()
                self._track_tokens(getattr(result, "token_usage", {}) or {})
                if name == "campaign_planner":
                    ranked = self._safe_json_parse(getattr(result, "raw", "[]"))
                    proposals_generated = len(ranked)
                    self._phase_results["target_proposals"] = ranked

        except Exception as exc:
            logger.error("Target phase failed: %s", exc)

        return {"proposals_generated": proposals_generated}

    # ------------------------------------------------------------------
    # Activate phase
    # ------------------------------------------------------------------

    def _run_activate_phase(
        self, brief_text: str, brief_id: Optional[int], **kwargs
    ) -> dict:
        """Run Activate: outreach_manager → creator_content_auditor → contract_helper → content_amplifier."""
        send = kwargs.get("send", False)
        dms_sent = 0
        try:
            from agents.activate.outreach_manager import (
                get_outreach_manager_agent,
                get_outreach_manager_task,
            )
            from agents.activate.creator_content_auditor import (
                get_creator_content_auditor_agent,
                get_creator_content_auditor_task,
            )
            from agents.activate.contract_helper import (
                get_contract_helper_agent,
                get_contract_helper_task,
            )
            from agents.activate.content_amplifier import (
                get_content_amplifier_agent,
                get_content_amplifier_task,
            )

            for get_agent, get_task, name in [
                (get_outreach_manager_agent, get_outreach_manager_task, "outreach_manager"),
                (get_creator_content_auditor_agent, get_creator_content_auditor_task, "creator_content_auditor"),
                (get_contract_helper_agent, get_contract_helper_task, "contract_helper"),
                (get_content_amplifier_agent, get_content_amplifier_task, "content_amplifier"),
            ]:
                agent = get_agent(send=send) if name == "outreach_manager" else get_agent()
                if name == "outreach_manager":
                    # Get proposals from phase results or from scout data
                    proposals_json = json.dumps(
                        self._phase_results.get("target_proposals", [])
                        or self._phase_results.get("scout_creators", [])
                    )
                    task = get_task(proposals_json, agent, brief_id=brief_id or 1, send=send)
                elif name == "creator_content_auditor":
                    task = get_task(brief_text, agent, brief_context=brief_text, creator_info="{}")
                elif name == "contract_helper":
                    task = get_task(brief_id or 1, agent, brief_id=brief_id or 1)
                elif name == "content_amplifier":
                    task = get_task("[]", agent, brief_context=brief_text)
                else:
                    task = get_task(brief_text, agent)

                self.crew = Crew(
                    agents=[agent],
                    tasks=[task],
                    process=Process.sequential,
                    verbose=True,
                )
                result = self.crew.kickoff()
                self._track_tokens(getattr(result, "token_usage", {}) or {})

                if name == "outreach_manager":
                    outreach_results = self._safe_json_parse(getattr(result, "raw", "[]"))
                    if not outreach_results:
                        try:
                            raw_text = result.json() if hasattr(result, "json") else ""
                            parsed = json.loads(raw_text) if raw_text else {}
                            if isinstance(parsed, dict) and "results" in parsed:
                                outreach_results = parsed["results"]
                        except (json.JSONDecodeError, TypeError):
                            pass
                    for r in outreach_results:
                        if r.get("sent"):
                            dms_sent += 1

        except Exception as exc:
            logger.error("Activate phase failed: %s", exc)

        return {"dms_sent": dms_sent, "dry_run": not send}

    # ------------------------------------------------------------------
    # Report phase
    # ------------------------------------------------------------------

    def _run_report_phase(
        self, brief_text: str, brief_id: Optional[int], **kwargs
    ) -> dict:
        """Run Report: landing_optimizer → performance_analyzer → roi_calculator → report_generator."""
        report_generated = False
        try:
            from agents.report.landing_optimizer import (
                get_landing_optimizer_agent,
                get_landing_optimizer_task,
            )
            from agents.report.performance_analyzer import (
                get_performance_analyzer_agent,
                get_performance_analyzer_task,
            )
            from agents.report.roi_calculator import (
                get_roi_calculator_agent,
                get_roi_calculator_task,
            )
            from agents.report.report_generator import (
                get_report_generator_agent,
                get_report_generator_task,
            )

            for get_agent, get_task, name in [
                (get_landing_optimizer_agent, get_landing_optimizer_task, "landing_optimizer"),
                (get_performance_analyzer_agent, get_performance_analyzer_task, "performance_analyzer"),
                (get_roi_calculator_agent, get_roi_calculator_task, "roi_calculator"),
                (get_report_generator_agent, get_report_generator_task, "report_generator"),
            ]:
                agent = get_agent()
                task = get_task(brief_text, agent)
                self.crew = Crew(
                    agents=[agent],
                    tasks=[task],
                    process=Process.sequential,
                    verbose=True,
                )
                result = self.crew.kickoff()
                self._track_tokens(getattr(result, "token_usage", {}) or {})

                if name == "landing_optimizer":
                    task = get_task(brief_text, agent)
                elif name == "report_generator":
                    report_generated = True

        except Exception as exc:
            logger.error("Report phase failed: %s", exc)

        return {"report_generated": report_generated}


# Backward compat: InfluencerCampaignCrew delegates to StarCrew
class InfluencerCampaignCrew(StarCrew):
    """Backward-compatible alias. kickoff() runs all phases like the old pipeline."""

    def kickoff(
        self,
        brief_text: str,
        send: bool = False,
        approve_each: bool = False,
        max_creators: int = 10,
    ) -> dict:
        """Run the full STAR pipeline (backward compat with old crew.py)."""
        result = self.run_all(brief_text, send=send, approve_each=approve_each, max_creators=max_creators)
        # Flatten to old summary shape for backward compat
        scout = result.get("scout", {})
        activate = result.get("activate", {})
        return {
            "brief_id": result.get("brief_id"),
            "creators_found": scout.get("creators_found", 0),
            "suggestions_saved": scout.get("suggestions_saved", 0),
            "dms_attempted": activate.get("dms_attempted", 0),
            "dms_sent": activate.get("dms_sent", 0),
            "dry_run": result.get("dry_run", True),
            "total_tokens": result.get("total_tokens", 0),
        }