"""Configuration loader for vernacular-creator-agents."""

from pathlib import Path

from dotenv import load_dotenv

# ---------------------------------------------------------------------------
# Load .env from project root (next to this file)
# ---------------------------------------------------------------------------
_env_path = Path(__file__).resolve().parent / ".env"
load_dotenv(_env_path)

import os  # noqa: E402

# ---------------------------------------------------------------------------
# Fireworks AI
# ---------------------------------------------------------------------------
FIREWORKS_API_KEY: str = os.getenv("FIREWORKS_API_KEY", "")
FIREWORKS_BASE_URL: str = os.getenv("FIREWORKS_BASE_URL", "https://api.fireworks.ai/inference/v1")

# ---------------------------------------------------------------------------
# Per-agent model paths / aliases
# ---------------------------------------------------------------------------
MODEL_DISCOVERY: str = os.getenv("MODEL_DISCOVERY", "accounts/fireworks/models/glm-5p2")
MODEL_PROPOSAL: str = os.getenv("MODEL_PROPOSAL", "accounts/fireworks/models/qwen3p7-plus")
MODEL_OUTREACH: str = os.getenv("MODEL_OUTREACH", "accounts/fireworks/models/qwen3p7-plus")
MODEL_NEGOTIATOR: str = os.getenv("MODEL_NEGOTIATOR", "accounts/fireworks/models/qwen3p7-plus")
MODEL_CONTRACT: str = os.getenv("MODEL_CONTRACT", "accounts/fireworks/models/glm-5p2")

# ---------------------------------------------------------------------------
# STAR phase model paths (v2 — 24-agent enrichment)
# ---------------------------------------------------------------------------
# Scout phase
MODEL_SCOUT_AUDIENCE: str = os.getenv("MODEL_SCOUT_AUDIENCE", "accounts/fireworks/models/glm-5p2")
MODEL_SCOUT_TREND: str = os.getenv("MODEL_SCOUT_TREND", "accounts/fireworks/models/glm-5p2")
MODEL_SCOUT_DISCOVERY: str = os.getenv("MODEL_SCOUT_DISCOVERY", "accounts/fireworks/models/glm-5p2")
MODEL_SCOUT_FIT: str = os.getenv("MODEL_SCOUT_FIT", "accounts/fireworks/models/glm-5p2")
# Target phase
MODEL_TARGET_COMPETITOR: str = os.getenv("MODEL_TARGET_COMPETITOR", "accounts/fireworks/models/glm-5p2")
MODEL_TARGET_PLANNER: str = os.getenv("MODEL_TARGET_PLANNER", "accounts/fireworks/models/glm-5p2")
MODEL_TARGET_BRIEF: str = os.getenv("MODEL_TARGET_BRIEF", "accounts/fireworks/models/glm-5p2")
MODEL_TARGET_BUDGET: str = os.getenv("MODEL_TARGET_BUDGET", "accounts/fireworks/models/glm-5p2")
# Activate phase
MODEL_ACTIVATE_OUTREACH: str = os.getenv("MODEL_ACTIVATE_OUTREACH", "accounts/fireworks/models/qwen3p7-plus")
MODEL_ACTIVATE_AUDITOR: str = os.getenv("MODEL_ACTIVATE_AUDITOR", "accounts/fireworks/models/glm-5p2")
MODEL_ACTIVATE_CONTRACT: str = os.getenv("MODEL_ACTIVATE_CONTRACT", "accounts/fireworks/models/glm-5p2")
MODEL_ACTIVATE_AMPLIFIER: str = os.getenv("MODEL_ACTIVATE_AMPLIFIER", "accounts/fireworks/models/qwen3p7-plus")
# Report phase
MODEL_REPORT_LANDING: str = os.getenv("MODEL_REPORT_LANDING", "accounts/fireworks/models/glm-5p2")
MODEL_REPORT_PERFORMANCE: str = os.getenv("MODEL_REPORT_PERFORMANCE", "accounts/fireworks/models/glm-5p2")
MODEL_REPORT_ROI: str = os.getenv("MODEL_REPORT_ROI", "accounts/fireworks/models/glm-5p2")
MODEL_REPORT_GENERATOR: str = os.getenv("MODEL_REPORT_GENERATOR", "accounts/fireworks/models/glm-5p2")
# Protocol phase
MODEL_PROTOCOL_REGISTRY: str = os.getenv("MODEL_PROTOCOL_REGISTRY", "accounts/fireworks/models/glm-5p2")

# ---------------------------------------------------------------------------
# Instagram credentials
# ---------------------------------------------------------------------------
IG_USERNAME: str = os.getenv("IG_USERNAME", "")
IG_PASSWORD: str = os.getenv("IG_PASSWORD", "")
IG_SESSION_FILE: str = os.getenv("IG_SESSION_FILE", "data/ig_session.json")

# ---------------------------------------------------------------------------
# Scraper data source
# ---------------------------------------------------------------------------
SCRAPER_DB_PATH: str = os.getenv("SCRAPER_DB_PATH", "")
SCRAPER_API_URL: str = os.getenv("SCRAPER_API_URL", "")

# ---------------------------------------------------------------------------
# State database
# ---------------------------------------------------------------------------
AGENTS_DB_PATH: str = os.getenv("AGENTS_DB_PATH", "data/agents.db")

# ---------------------------------------------------------------------------
# Safety / rate-limit constants  (fallback defaults)
# ---------------------------------------------------------------------------
MAX_DMS_PER_DAY: int = int(os.getenv("MAX_DMS_PER_DAY", "20"))
DM_DELAY_SECONDS: int = int(os.getenv("DM_DELAY_SECONDS", "5"))
DM_DELAY_JITTER: int = int(os.getenv("DM_DELAY_JITTER", "3"))

# Derived: randomized delay window [MIN, MAX], clamped >= 0
DM_DELAY_MIN: int = max(DM_DELAY_SECONDS - DM_DELAY_JITTER, 0)
DM_DELAY_MAX: int = max(DM_DELAY_SECONDS + DM_DELAY_JITTER, 0)

MAX_NEGOTIATION_ROUNDS: int = int(os.getenv("MAX_NEGOTIATION_ROUNDS", "3"))
BUDGET_OVERRUN_PERCENT: int = int(os.getenv("BUDGET_OVERRUN_PERCENT", "120"))
MAX_PROFILE_FETCHES_PER_RUN: int = int(os.getenv("MAX_PROFILE_FETCHES_PER_RUN", "50"))

# Token budget constants
MAX_TOKENS_PER_AGENT: int = int(os.getenv("MAX_TOKENS_PER_AGENT", "4000"))
MAX_TOTAL_TOKENS_PER_RUN: int = int(os.getenv("MAX_TOTAL_TOKENS_PER_RUN", "25000"))

CONNECTOR_TIMEOUT_SECONDS: int = int(os.getenv("CONNECTOR_TIMEOUT_SECONDS", "30"))

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")