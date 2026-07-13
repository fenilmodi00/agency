"""Sequential crew orchestration for the vernacular-creator-agents pipeline.

Discovery → Proposal → Outreach (no Negotiator / Contract).
"""

import json
import logging
from typing import Optional

from config import AGENTS_DB_PATH, MAX_TOTAL_TOKENS_PER_RUN
from database import Database
from llm_client import get_token_usage

logger = logging.getLogger(__name__)

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


class InfluencerCampaignCrew:
    """Orchestrates Discovery → Proposal → Outreach sequentially.

    Does NOT include Negotiator or Contract stages.
    """

    def __init__(self):
        # Lazy-load agents — imports happen in kickoff, not here.
        self._db: Optional[Database] = None
        self._crew: Optional[Crew] = None
        self._total_tokens: int = 0

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
    # Public API
    # ------------------------------------------------------------------

    def kickoff(
        self,
        brief_text: str,
        send: bool = False,
        approve_each: bool = False,
        max_creators: int = 10,
    ) -> dict:
        """Run the full Discovery → Proposal → Outreach pipeline.

        Returns a summary dict with brief_id, creators_found,
        suggestions_saved, dms_attempted, dms_sent, dry_run, total_tokens.
        """
        db = self._get_db()
        self._total_tokens = 0

        # 1. Insert brand brief
        try:
            brief_id = db.insert_brief(raw_brief=brief_text)
        except Exception as exc:
            logger.error("Failed to insert brand brief: %s", exc)
            return {
                "brief_id": None,
                "creators_found": 0,
                "suggestions_saved": 0,
                "dms_attempted": 0,
                "dms_sent": 0,
                "dry_run": not send,
                "total_tokens": self._total_tokens,
            }

        # 2. Discovery
        ranked_creators = []
        try:
            from agents.discovery import get_discovery_agent, get_discovery_task

            discovery_agent = get_discovery_agent()
            discovery_task = get_discovery_task(brief_text, discovery_agent)

            self.crew = Crew(
                agents=[discovery_agent],
                tasks=[discovery_task],
                process=Process.sequential,
                verbose=True,
            )
            result = self.crew.kickoff()
            self._track_tokens(getattr(result, "token_usage", {}) or {})

            ranked_creators = self._safe_json_parse(getattr(result, "raw", "[]"))
            # Also try .json() method on result
            if not ranked_creators:
                ranked_creators = self._safe_json_parse(result.json() if hasattr(result, "json") else "[]")
        except Exception as exc:
            logger.error("Discovery task failed: %s", exc)

        creators_found = len(ranked_creators)
        logger.info("Discovery found %d creators", creators_found)

        # Limit to max_creators
        if len(ranked_creators) > max_creators:
            ranked_creators = ranked_creators[:max_creators]

        # 3. Insert campaign_suggestions
        suggestions_saved = 0
        for creator in ranked_creators:
            try:
                db.insert_suggestion(
                    brief_id=brief_id,
                    creator_username=creator.get("username", ""),
                    fit_score=creator.get("fit_score"),
                    match_reason=creator.get("match_reason"),
                    outreach_message=None,
                    campaign_ideas=None,
                )
                suggestions_saved += 1
            except Exception as exc:
                logger.error(
                    "Failed to insert suggestion for %s: %s",
                    creator.get("username", "?"),
                    exc,
                )

        # 4. Proposal
        proposals_json_str = json.dumps(ranked_creators)
        proposals = []
        try:
            from agents.proposal import get_proposal_agent, get_proposal_task

            proposal_agent = get_proposal_agent()
            proposal_task = get_proposal_task(proposals_json_str, proposal_agent)

            self.crew = Crew(
                agents=[proposal_agent],
                tasks=[proposal_task],
                process=Process.sequential,
                verbose=True,
            )
            result = self.crew.kickoff()
            self._track_tokens(getattr(result, "token_usage", {}) or {})

            proposals = self._safe_json_parse(getattr(result, "raw", "[]"))
            if not proposals:
                proposals = self._safe_json_parse(result.json() if hasattr(result, "json") else "[]")
        except Exception as exc:
            logger.error("Proposal task failed: %s", exc)

        # Build merged proposals: attach username from ranked_creators if missing
        creator_map = {c.get("username"): c for c in ranked_creators}
        for p in proposals:
            uname = p.get("creator_username") or p.get("username", "")
            if uname and uname in creator_map and "username" not in p:
                p["username"] = uname

        # 5. Outreach
        dms_attempted = 0
        dms_sent = 0
        try:
            from agents.outreach import get_outreach_agent, get_outreach_task

            outreach_agent = get_outreach_agent(send=send)
            outreach_task = get_outreach_task(
                proposals_json=json.dumps(proposals),
                agent=outreach_agent,
                brief_id=brief_id,
                send=send,
            )

            if approve_each and proposals:
                # Per-creator approval loop
                approved_proposals = []
                skipped = []
                for p in proposals:
                    uname = p.get("creator_username") or p.get("username", "(unknown)")
                    try:
                        response = input(
                            f"Send outreach DM to @{uname}? (Y/n): "
                        ).strip().lower()
                    except (EOFError, KeyboardInterrupt):
                        # Non-interactive or interrupted — skip approval
                        response = "y"

                    if response in ("", "y", "yes"):
                        approved_proposals.append(p)
                    else:
                        skipped.append(p)
                        logger.info("User declined outreach for @%s", uname)

                if approved_proposals:
                    self.crew = Crew(
                        agents=[outreach_agent],
                        tasks=[get_outreach_task(
                            proposals_json=json.dumps(approved_proposals),
                            agent=outreach_agent,
                            brief_id=brief_id,
                            send=send,
                        )],
                        process=Process.sequential,
                        verbose=True,
                    )
                    result = self.crew.kickoff()
                    self._track_tokens(getattr(result, "token_usage", {}) or {})

                    outreach_results = self._safe_json_parse(
                        getattr(result, "raw", "[]")
                    )
                    if not outreach_results:
                        try:
                            raw_text = result.json() if hasattr(result, "json") else ""
                            parsed = json.loads(raw_text) if raw_text else {}
                            if isinstance(parsed, dict) and "results" in parsed:
                                outreach_results = parsed["results"]
                        except (json.JSONDecodeError, TypeError):
                            pass

                    for r in outreach_results:
                        dms_attempted += 1
                        if r.get("sent"):
                            dms_sent += 1
            else:
                # No per-creator approval — run with all proposals
                self.crew = Crew(
                    agents=[outreach_agent],
                    tasks=[outreach_task],
                    process=Process.sequential,
                    verbose=True,
                )
                result = self.crew.kickoff()
                self._track_tokens(getattr(result, "token_usage", {}) or {})

                # Parse outreach results
                outreach_results = self._safe_json_parse(
                    getattr(result, "raw", "[]")
                )
                if not outreach_results:
                    try:
                        raw_text = result.json() if hasattr(result, "json") else ""
                        parsed = json.loads(raw_text) if raw_text else {}
                        if isinstance(parsed, dict) and "results" in parsed:
                            outreach_results = parsed["results"]
                    except (json.JSONDecodeError, TypeError):
                        pass

                for r in outreach_results:
                    dms_attempted += 1
                    if r.get("sent"):
                        dms_sent += 1

        except Exception as exc:
            logger.error("Outreach task failed: %s", exc)

        return {
            "brief_id": brief_id,
            "creators_found": creators_found,
            "suggestions_saved": suggestions_saved,
            "dms_attempted": dms_attempted,
            "dms_sent": dms_sent,
            "dry_run": not send,
            "total_tokens": self._total_tokens,
        }