# agents/ — STAR Framework Agent Definitions

The system uses a 24-agent STAR framework organized into 4 execution phases and a protocol registry.

## PHASE STRUCTURE

### 1. Scout (Discovery & Filtering)
Focused on identifying high-fit creators from the scraper database.
- **Goal**: Find regional creators matching the brand brief.
- **Key Tasks**: Querying DB, fit scoring, ranking.

### 2. Target (Content Analysis & Strategy)
Deep-dives into creator content to personalize the approach.
- **Goal**: Develop tailored campaign ideas for each identified creator.
- **Key Tasks**: Content summarization, post analysis, budget strategy.

### 3. Activate (Personalized Outreach)
Handles the actual communication.
- **Goal**: Send personalized, vernacular DMs.
- **Key Tasks**: Language detection, DM composition, quota management.

### 4. Report (Campaign Analytics)
Summarizes the results of the outreach.
- **Goal**: Provide campaign health and success metrics.
- **Key Tasks**: Conversion tracking, outcome summaries.

### Protocol Registry
8 specialized agents that manage system state, routing, and coordination between phases.

## BACKWARD COMPATIBILITY SHIMS
The following files are maintained as thin shims for legacy support, delegating work to the STAR agents:
- `discovery.py` → Scout
- `proposal.py` → Target
- `outreach.py` → Activate

## OTHER AGENTS
- `negotiator.py`: Rate Negotiator (runs via `check_replies.py`)
- `contract.py`: Contract Drafter (runs via `check_replies.py`)

## CONVENTIONS
- **Shared Utilities**: All STAR agents use `agents/_base.py` for Agent/Task stubs and prompt parsing.
- **No direct DB/IG access**: All persistence and API calls go through `tools/`.
- **Prompts**: Defined in `prompts/` with strict JSON schemas.
