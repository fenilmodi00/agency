# Vernacular Creator Agents

Automated influencer campaign pipeline that discovers regional content creators, generates personalized campaign proposals, and sends outreach DMs in their native language (Gujarati, Hindi, or English) through Instagram.

Built for a non-technical founder to run campaigns with minimal manual effort. You describe what you need in plain English. The agents handle the rest.

## What It Does

1. You write a brand brief describing your campaign (product, target audience, budget, language preferences).
2. The system finds matching creators from a scraped database and ranks them by fit.
3. It generates tailored campaign proposals for each creator, studying their recent content.
4. It composes and sends personalized DMs in the creator's preferred language.
5. When creators reply, a separate process reads their responses, negotiates rates, and generates ASCI-compliant contracts.

## Setup

### Prerequisites

- Python 3.11 or later
- A Fireworks AI API key (for LLM inference)
- Instagram account credentials (for sending DMs)
- A creator scraper database (SQLite or HTTP API)

### Installation

```bash
git clone <repository-url>
cd vernacular-creator-agents
pip install -r requirements.txt
```

### Configuration

Copy the example environment file and fill in your credentials:

```bash
cp .env.example .env
```

Open `.env` in a text editor and set these values:

| Variable | What It Is |
|---|---|
| `FIREWORKS_API_KEY` | Your Fireworks AI API key |
| `IG_USERNAME` | Instagram account username |
| `IG_PASSWORD` | Instagram account password |
| `SCRAPER_DB_PATH` | Path to the creator scraper SQLite database |
| `AGENTS_DB_PATH` | Where to store the agents' own database (default: `data/agents.db`) |

The `.env` file also has safety thresholds you can tune:

| Variable | Default | What It Controls |
|---|---|---|
| `MAX_DMS_PER_DAY` | 20 | Maximum DMs sent per day |
| `DM_DELAY_SECONDS` | 5 | Delay between DMs (seconds) |
| `DM_DELAY_JITTER` | 3 | Random jitter added to delay |
| `MAX_NEGOTIATION_ROUNDS` | 3 | Max back-and-forth rounds per creator |
| `MAX_TOKENS_PER_AGENT` | 4000 | Token budget per agent call |
| `MAX_TOTAL_TOKENS_PER_RUN` | 25000 | Total token budget per pipeline run |

## Usage

### Dry Run (default, no DMs sent)

Always start with a dry run to see what the agents would do without actually messaging anyone:

```bash
python main.py "Looking for Gujarati food creators with 10k-50k followers for a spice brand campaign, budget 50000 INR"
```

This runs the full pipeline (Discovery, Proposal, Outreach) but stops before sending any DMs. You'll see a campaign summary showing how many creators were found, proposals generated, and messages composed.

### Live Send

When you're satisfied with the dry run, add `--send` to actually dispatch DMs:

```bash
python main.py "Your brief here" --send
```

### Approve Each DM

For extra caution, combine `--send` with `--approve-each` to review every message before it goes out:

```bash
python main.py "Your brief here" --send --approve-each
```

The system will pause before each DM and ask you to confirm.

### Limit Creators

Process a smaller batch with `--max-creators`:

```bash
python main.py "Your brief here" --max-creators 5
```

### Checking Replies

After sending outreach, run the reply checker to process creator responses:

```bash
python check_replies.py
```

This reads Instagram DM threads for new replies, runs the Negotiator agent to decide next steps (accept, counter-offer, wait, escalate), and generates contracts when deals are accepted.

Use `--dry-run` to check without calling Instagram APIs:

```bash
python check_replies.py --dry-run
```

Schedule this to run periodically (e.g., via cron or Task Scheduler) to stay on top of creator responses.

## Safety

This system sends real messages to real people. Several safeguards are built in:

**Dry-run by default.** Running `python main.py` without `--send` never touches Instagram. No DMs are sent. No API calls are made. You see exactly what would happen.

**Per-message approval.** The `--approve-each` flag makes the system pause and ask you to confirm every single DM before sending. Use this when running your first few campaigns.

**DM rate limits.** The system enforces `MAX_DMS_PER_DAY` (default: 20) and adds randomized delays between messages (`DM_DELAY_SECONDS` +/- `DM_DELAY_JITTER`) to avoid triggering Instagram's spam detection.

**Token budgets.** Each agent call is capped at `MAX_TOKENS_PER_AGENT` tokens, and the entire pipeline run is capped at `MAX_TOTAL_TOKENS_PER_RUN` tokens. This prevents runaway API costs.

**Session file protection.** The Instagram session file (`data/ig_session.json`) stores authentication tokens. Keep it private. It's listed in `.gitignore` so it won't be committed to version control. Set restrictive file permissions:

```bash
chmod 600 data/ig_session.json
```

**Quota enforcement.** Before every DM, the Outreach agent checks the daily quota. If the limit is reached, it stops immediately and reports which creators were skipped.

## Architecture

```
                    +------------------+
                    |   Brand Brief    |
                    |  (your input)    |
                    +--------+---------+
                             |
                             v
                    +------------------+
                    |    Discovery     |
                    |    Agent         |
                    |                  |
                    | - Query scraper  |
                    | - Score fit      |
                    | - Rank creators  |
                    +--------+---------+
                             |
                             v
                    +------------------+
                    |    Proposal      |
                    |    Agent         |
                    |                  |
                    | - Read content   |
                    | - Craft ideas    |
                    | - Set budgets    |
                    +--------+---------+
                             |
                             v
                    +------------------+
                    |    Outreach      |
                    |    Agent         |
                    |                  |
                    | - Detect language|
                    | - Compose DM     |
                    | - Send (or dry)  |
                    +--------+---------+
                             |
                             v
                    +------------------+
                    | Instagram DM     |
                    | (if --send)      |
                    +--------+---------+
                             |
                    (later, when creator replies)
                             |
                             v
                    +------------------+
                    |   Negotiator     |
                    |    Agent         |
                    |                  |
                    | - Read replies   |
                    | - Decide action  |
                    | - Counter/accept |
                    +--------+---------+
                             |
                             v
                    +------------------+
                    |    Contract      |
                    |    Agent         |
                    |                  |
                    | - Generate terms |
                    | - ASCI compliance|
                    | - Bilingual      |
                    +------------------+
```

The main pipeline (`main.py`) runs Discovery, Proposal, and Outreach in sequence. The reply checker (`check_replies.py`) runs Negotiator and Contract when creators respond.

## Project Structure

```
vernacular-creator-agents/
  main.py              # CLI entry point for the campaign pipeline
  check_replies.py     # Scheduled task for processing creator replies
  crew.py              # Sequential crew orchestration
  config.py            # Configuration loader (.env)
  database.py          # SQLite database schema and operations
  ig_client.py         # Instagram client wrapper (instagrapi)
  llm_client.py        # Fireworks AI LLM client
  agents/
    discovery.py       # Creator discovery and fit scoring
    proposal.py        # Campaign proposal generation
    outreach.py        # DM composition and sending
    negotiator.py      # Rate negotiation
    contract.py        # Contract generation
  tools/
    scraper_tools.py   # Creator database queries
    instagram_tools.py # Instagram DM operations
    database_tools.py  # State management
    calculation_tools.py # Fit score calculation
    llm_tools.py       # LLM utility functions
  prompts/             # Agent prompt templates
  data/                # Runtime data (database, session, logs)
  tests/               # Test suite
```

## Running Tests

```bash
pytest
```

## Logs

All runs are logged to `data/run.log` with rotation at 10 MB and 1 week retention. Console output uses the log level set in `LOG_LEVEL` (default: `INFO`).
