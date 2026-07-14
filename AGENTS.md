# Agent Reference

Five agents work in sequence to run an influencer campaign. This document describes each agent's role, tools, inputs, outputs, and failure modes. It also covers operational guidance for restarts, Instagram challenges, and log reading.

---

## 1. Discovery Agent

**Role:** Creator Discovery Specialist

**Goal:** Find the best-matching vernacular creators for a brand brief by querying the scraper database, scoring each creator for fit, and returning a ranked shortlist.

**Model:** `MODEL_DISCOVERY` (default: `accounts/fireworks/models/glm-5p2`)

**Tools:**
- `query_creators` - Search the scraper database for creators matching criteria
- `get_creator_details` - Fetch detailed profile info for a specific creator
- `calculate_fit_score` - Compute a weighted 0-100 fit score between a creator and the brief

**Input:** Raw brand brief text describing the campaign (product, audience, budget, language, follower range).

**Output:** JSON array sorted by `fit_score` descending:
```json
[
  {
    "username": "creator_handle",
    "fit_score": 87,
    "match_reason": "Strong food content in Gujarati, audience overlaps with target demo"
  }
]
```

**Failure Modes:**
- **Scraper database unavailable.** If `SCRAPER_DB_PATH` is wrong or the file doesn't exist, `query_creators` returns empty results. The agent produces an empty array. Check that the scraper DB path in `.env` is correct.
- **Brief too vague.** If the brief lacks specifics (no language, no follower range), the agent may return a broad, unranked list. Write specific briefs.
- **LLM returns malformed JSON.** The crew parser strips markdown fences and attempts recovery, but if the model returns completely invalid output, the result is an empty list. Check `data/run.log` for parse errors.
- **Token budget exceeded.** If `MAX_TOKENS_PER_AGENT` is too low for the number of creators in the database, the agent may truncate its output. Increase the budget or limit creators with `--max-creators`.

---

## 2. Proposal Agent

**Role:** Proposal Strategist

**Goal:** Generate detailed campaign proposals for each creator in the shortlist by analyzing their content summary and recent posts.

**Model:** `MODEL_PROPOSAL` (default: `accounts/fireworks/models/qwen3p7-plus`)

**Tools:**
- `get_creator_content_summary` - Get post types, average views, engagement metrics
- `get_creator_recent_posts` - Get recent post content for context

**Input:** JSON array of creators from the Discovery agent (with `username`, `fit_score`, `match_reason`).

**Output:** JSON array of proposals:
```json
[
  {
    "creator_username": "creator_handle",
    "campaign_ideas": ["Recipe video series using the brand's spice mix"],
    "deliverables": ["3 Reels over 2 weeks", "1 carousel post"],
    "suggested_budget": 8000,
    "timeline": "2 weeks from agreement",
    "notes": "Creator typically posts on Tuesdays and Fridays"
  }
]
```

**Failure Modes:**
- **Creator has no content data.** If the scraper database has no posts for a creator, the agent generates a generic proposal. These proposals tend to be less specific and may not convert well.
- **Budget miscalculation.** The agent estimates budgets based on creator profile data. These are starting points, not final rates. The Negotiator agent handles actual rate discussions.
- **LLM hallucination.** The agent might invent content trends or engagement numbers not in the data. Proposals should be reviewed before sending, especially on first campaigns.

---

## 3. Outreach Agent

**Role:** Vernacular Creator Outreach Specialist

**Goal:** Compose personalized DMs in each creator's preferred language and send them (or save for review in dry-run mode).

**Model:** `MODEL_OUTREACH` (default: `accounts/fireworks/models/qwen3p7-plus`)

**Tools:**
- `get_creator_language` - Detect the creator's preferred language (Gujarati, Hindi, English)
- `check_dm_quota` - Check if daily DM limit has been reached
- `send_instagram_dm` - Send a DM via Instagram (only called when `send=True`)
- `save_conversation` - Save conversation state to the database
- `log_dm` - Log the DM for audit trail

**Input:** JSON array of proposals from the Proposal agent, plus `SEND_MODE` (true/false) and `BRIEF_ID`.

**Output:** JSON object:
```json
{
  "results": [
    {
      "username": "creator_handle",
      "thread_id": "ig_thread_123",
      "language": "gu",
      "message": "નમસ્તે! અમે તમારી સાથે કામ કરવા માંગીએ છીએ...",
      "sent": true,
      "dry_run": false
    }
  ],
  "quota_exceeded": false
}
```

**Failure Modes:**
- **DM quota exhausted.** The agent checks quota before every send. When the limit is hit, it stops and sets `quota_exceeded: true`. Remaining creators are skipped. Wait until the next day or raise `MAX_DMS_PER_DAY`.
- **Instagram rate limit / challenge.** Instagram may block sends if too many DMs go out too fast. The system adds randomized delays (`DM_DELAY_SECONDS` +/- `DM_DELAY_JITTER`) to reduce this risk. If blocked, the session may need re-authentication (see Operational Guidance below).
- **Language detection fails.** If `get_creator_language` returns empty, the agent defaults to English. The message still sends but may feel less personal.
- **Send failure.** Network errors or invalid usernames cause individual sends to fail. The agent records the error and continues with the next creator. Check logs for `send_instagram_dm` errors.

---

## 4. Negotiator Agent

**Role:** Rate Negotiator

**Goal:** Read creator replies in Instagram DM threads, decide the next action (accept, counter-offer, wait, escalate, give up), and send response messages in the creator's language.

**Model:** `MODEL_NEGOTIATOR` (default: `accounts/fireworks/models/qwen3p7-plus`, configured as `deepseek-v4-pro` in `.env.example`)

**Tools:**
- `read_instagram_threads` - List active DM threads
- `read_thread_messages` - Read messages in a specific thread
- `send_instagram_dm` - Send counter-offer or acceptance message
- `get_conversation_history` - Load past negotiation rounds from the database
- `update_conversation_negotiation` - Save negotiation state
- `get_brand_budget` - Check the brand's budget ceiling
- `check_dm_quota` - Verify DM quota before sending
- `log_dm` - Log sent/received messages

**Input:** Conversation record from the database (creator username, thread ID, current status, message count, negotiation history).

**Output:** JSON object:
```json
{
  "action": "counter",
  "response": "અમે તમારી કિંમત વિશે વિચારીએ છીએ...",
  "agreed_rate": null,
  "round_number": 2,
  "status": "open"
}
```

Actions: `accept`, `counter`, `wait`, `escalate`, `give_up`.

**Failure Modes:**
- **Negotiation exceeds max rounds.** When `round_number > MAX_NEGOTIATION_ROUNDS`, the agent should escalate or give up. If it doesn't, manually review the conversation in the database.
- **Budget overrun.** If the creator's rate exceeds `BUDGET_OVERRUN_PERCENT` of the proposal budget, the agent should escalate. Check `get_brand_budget` output.
- **Thread read failure.** If Instagram API fails to return thread messages, the agent has no context to negotiate from. It defaults to `action: wait`. Retry on the next `check_replies.py` run.
- **DM quota blocks counter-offer.** The agent checks quota before sending. If exhausted, it logs a warning and skips the send. The conversation stays in `open` status.

---

## 5. Contract Agent

**Role:** Contract Drafter

**Goal:** Generate a bilingual collaboration agreement (English + Gujarati summary) that complies with ASCI (Advertising Standards Council of India) guidelines.

**Model:** `MODEL_CONTRACT` (default: `accounts/fireworks/models/glm-5p2`)

**Tools:**
- `get_conversation_details` - Load the accepted conversation terms
- `get_brand_brief` - Load the original brand brief
- `save_contract` - Save the generated contract to the database

**Input:** Conversation record with agreed rate, creator username, and brief ID.

**Output:** JSON object:
```json
{
  "contract_id": 42,
  "contract_text": "Full English contract text...",
  "gujarati_summary": "ગુજરાતીમાં સારાંશ...",
  "contract_type": "single_post",
  "deliverables": ["1 Reel", "1 Story"],
  "usage_rights": "Brand can use content for 3 months",
  "timeline": "Content due within 14 days",
  "asci_compliant": true
}
```

**Failure Modes:**
- **Missing conversation data.** If the conversation doesn't have an agreed rate or accepted status, the agent can't generate a contract. Ensure the Negotiator set `action: accept` first.
- **ASCI non-compliance.** The agent aims for compliance but generates templates, not legal documents. All contracts need human legal review before signing.
- **Gujarati translation quality.** The LLM-generated Gujarati summary may have grammatical issues. For high-value deals, have a native speaker review.

---

## Operational Guidance

### How to Restart After a Failure

The pipeline is sequential and stateful. Each stage writes to the SQLite database at `AGENTS_DB_PATH`.

**If Discovery fails:** No data is written. Just re-run `main.py` with the same brief. The brief is re-inserted with a new ID.

**If Proposal fails:** Discovery results are saved in `campaign_suggestions`. Re-running `main.py` creates a new brief and starts from scratch. To resume, you'd need to query the database directly.

**If Outreach fails partway through:** Some DMs may have been sent. The database tracks which conversations reached `outreach_sent` status. Re-running with `--send` will attempt all creators again, but the DM quota check prevents double-sending to the same creator on the same day.

**If check_replies.py fails:** It's safe to re-run. The script checks message counts and only processes conversations with new messages. Already-processed conversations are skipped.

### How to Handle Instagram Challenges

Instagram may present challenges (CAPTCHA, login verification, temporary blocks) when it detects automated activity.

**Session file.** Authentication state is stored in `data/ig_session.json`. If Instagram invalidates the session, delete this file and re-run. The system will perform a fresh login using `IG_USERNAME` and `IG_PASSWORD`.

**Temporary blocks.** If DMs fail with rate-limit errors, stop sending for 24 hours. The daily quota (`MAX_DMS_PER_DAY`) helps prevent this, but Instagram's internal limits are opaque.

**Reduce risk.** Keep `DM_DELAY_SECONDS` at 5 or higher. Keep `MAX_DMS_PER_DAY` at 20 or lower. Avoid running the pipeline multiple times per day.

**Two-factor authentication.** If your Instagram account has 2FA enabled, `instagrapi` may need the verification code during login. Check the console output for prompts.

### How to Read Logs

**Console output.** Real-time log messages appear on stderr with timestamps, log levels, and module names. Color-coded when running in a terminal.

**Log file.** All output is also written to `data/run.log`. This file rotates at 10 MB and keeps 1 week of history. Older logs are automatically deleted.

**Key log patterns to watch for:**

| Pattern | Meaning |
|---|---|
| `Discovery found N creators` | How many creators matched the brief |
| `DM quota exhausted` | Daily send limit reached, remaining creators skipped |
| `Failed to parse` | LLM returned output the system couldn't read as JSON |
| `Token budget exceeded` | Pipeline used more tokens than `MAX_TOTAL_TOKENS_PER_RUN` |
| `Instagram client initialised` | Login succeeded, ready to send DMs |
| `No new replies` | check_replies found no new messages in a thread |
| `Deal accepted! Rate: N` | Negotiator agreed to a creator's rate |
| `Contract generated: id=N` | Contract agent saved a new contract |

**Debug mode.** Set `LOG_LEVEL=DEBUG` in `.env` for verbose output including full tool call arguments and LLM responses. This is noisy but useful when an agent behaves unexpectedly.
