# Research Notes

Technical research that informed the architecture and implementation of vernacular-creator-agents. Each section covers a key technology choice with references.

---

## CrewAI Agent Orchestration

### Why CrewAI

We evaluated several multi-agent frameworks (AutoGen, LangGraph, CrewAI) and chose CrewAI for its sequential process model and simple agent/task abstraction. Our pipeline is inherently sequential: Discovery feeds into Proposal feeds into Outreach. CrewAI's `Process.sequential` maps directly to this flow without requiring custom graph definitions.

### Architecture Decisions

**One agent per stage.** Each agent has a single responsibility, its own tool set, and its own prompt. This makes debugging easier: when something goes wrong, you know which agent to look at.

**No inter-agent delegation.** All agents have `allow_delegation=False`. Delegation adds unpredictability. We want a deterministic pipeline where each stage runs exactly once in order.

**Crew re-instantiation per stage.** The `InfluencerCampaignCrew` creates a new `Crew` object for each stage (Discovery, Proposal, Outreach) rather than building one Crew with all tasks. This gives us finer control over error handling and token tracking per stage.

**JSON output enforcement.** Every task's `expected_output` specifies a JSON schema. The crew module includes a `_safe_json_parse` helper that strips markdown fences and handles common LLM formatting issues. This is a pragmatic choice: LLMs don't always produce clean JSON, and we need reliable parsing.

### Key Documentation

- CrewAI docs: https://docs.crewai.com/introduction
- CrewAI agents: https://docs.crewai.com/concepts/agents
- CrewAI tasks: https://docs.crewai.com/concepts/tasks
- CrewAI processes: https://docs.crewai.com/concepts/crews
- CrewAI tools: https://docs.crewai.com/concepts/tools

### Token Management

CrewAI doesn't expose per-agent token counting natively. We track tokens by reading `result.token_usage` after each `crew.kickoff()` call and accumulating in `InfluencerCampaignCrew._total_tokens`. When the total exceeds `MAX_TOTAL_TOKENS_PER_RUN`, a warning is logged. This is a soft limit: the pipeline doesn't stop, but the operator knows costs are climbing.

---

## instagrapi DM Capabilities

### Why instagrapi

`instagrapi` is the most maintained Python library for Instagram's private API. It supports DM operations (send, read threads, read messages) that the official Instagram Graph API doesn't expose for personal accounts.

### DM Operations Used

**`client.direct_send(text, user_ids)`** - Send a DM to one or more users. Returns a thread object with `id` (the thread ID we store in the database).

**`client.direct_threads()`** - List all DM threads. Used to find existing conversations with creators.

**`client.direct_messages(thread_id, amount)`** - Read messages in a thread. Used by `check_replies.py` to detect new replies.

### Session Management

instagrapi caches authentication state in a session file (`data/ig_session.json`). This avoids re-login on every run, which is important because Instagram rate-limits login attempts. The session file contains cookies and device tokens. It must be kept private (hence `.gitignore`).

### Known Limitations

**Rate limits.** Instagram's private API has undocumented rate limits for DMs. Our defaults (20 DMs/day, 5-second delays with 3-second jitter) are conservative estimates based on community reports. These may need adjustment for your account's age and trust level.

**Challenge handling.** Instagram may present CAPTCHAs or verification challenges during login. instagrapi has some built-in challenge resolution, but complex challenges (phone verification, backup codes) may require manual intervention.

**API stability.** Instagram periodically changes its private API. instagrapi updates to track these changes, but breakage can happen. Pin the instagrapi version in `requirements.txt` and watch for updates.

**No official support.** This uses Instagram's private API, which violates Instagram's Terms of Service. The account used for sending DMs risks suspension. Use a dedicated account, not a personal one.

### Key Documentation

- instagrapi GitHub: https://github.com/subzeroid/instagrapi
- instagrapi DM docs: https://subzeroid.github.io/instagrapi/direct.html
- Instagram private API risks: https://help.instagram.com/482670218583415

---

## Fireworks AI Model Selection for Gujarati/Hindi

### Why Fireworks AI

Fireworks AI provides low-latency inference for open-weight models with an OpenAI-compatible API. We use it because:

1. **Model variety.** Multiple models available through a single API, so we can assign different models to different agents based on their needs.
2. **Cost.** Significantly cheaper than closed-model APIs (GPT-4, Claude) for the volume of calls our pipeline makes.
3. **OpenAI compatibility.** The `openai` Python SDK works with Fireworks by changing the `base_url`. Minimal code changes.

### Model Assignments

| Agent | Model | Rationale |
|---|---|---|
| Discovery | `glm-5p2` | Structured output (JSON arrays), doesn't need creative language. Fast and cheap. |
| Proposal | `qwen3p7-plus` | Needs to analyze content and generate creative campaign ideas. Better reasoning. |
| Outreach | `qwen3p7-plus` | Must compose messages in Gujarati/Hindi with cultural nuance. Strong multilingual capability. |
| Negotiator | `deepseek-v4-pro` | Complex reasoning about rates, budgets, and negotiation strategy. Needs strong logic. |
| Contract | `glm-5p2` | Template generation with specific structure. Doesn't need creativity. |

### Gujarati and Hindi Capability

Vernacular language support was a key selection criterion. Our agents must compose outreach messages and negotiate in Gujarati and Hindi.

**Qwen models** (used for Proposal and Outreach) have strong multilingual training data including Indian languages. They handle Gujarati script (Gujarati Unicode block U+0A80-U+0AFF) and Devanagari (U+0900-U+097F) well.

**GLM models** (used for Discovery and Contract) have adequate vernacular support for structured tasks but may produce less natural-sounding prose. This is acceptable for Discovery (which outputs JSON, not prose) and Contract (which generates English-first with a Gujarati summary).

**DeepSeek models** (used for Negotiator) have strong reasoning in multilingual contexts. The negotiation task requires understanding a creator's counter-offer (possibly in Gujarati) and composing a response in the same language.

### Prompting for Vernacular Output

We include explicit language instructions in agent prompts. The Outreach agent calls `get_creator_language` first, then composes the message in that language. The prompt says:

> "Write a warm, concise outreach message in the creator's language."

This works but isn't perfect. The LLM sometimes mixes English and vernacular (code-switching), which is actually natural for informal Instagram DMs in India. For formal contracts, the Contract agent produces English text with a separate Gujarati summary.

### Key Documentation

- Fireworks AI docs: https://docs.fireworks.ai/getting-started/introduction
- Fireworks model list: https://fireworks.ai/models
- OpenAI-compatible API: https://docs.fireworks.ai/getting-started/openai-compatible-api
- Qwen multilingual capabilities: https://qwenlm.github.io/blog/qwen2.5/
- Fireworks pricing: https://fireworks.ai/pricing

---

## ASCI Influencer Marketing Guidelines

### What is ASCI

The Advertising Standards Council of India (ASCI) is the self-regulatory body for advertising in India. In 2022, ASCI issued specific guidelines for influencer marketing, making it one of the first countries to formalize these rules.

### Key Requirements for Our Contracts

**Disclosure.** Every sponsored post must be clearly labeled with `#ad`, `#sponsored`, or `#collaboration`. The Contract agent includes ASCI disclosure placeholders in every generated contract.

**Platform-specific disclosure.** On Instagram, the disclosure must be visible without clicking "more". This means the `#ad` tag must appear in the first line of the caption, not buried at the end.

**Content guidelines.** Influencer content must not:
- Make unsubstantiated claims about the product
- Target minors for certain product categories (alcohol, tobacco, gambling)
- Mislead consumers about the nature of the endorsement

**Brand responsibility.** The brand (our client) is responsible for ensuring the influencer complies with disclosure requirements. This is why our contracts include explicit disclosure clauses.

### How We Implement Compliance

**Contract templates.** The Contract agent generates contracts with these ASCI-required sections:
- Disclosure requirements (specific hashtags, placement)
- Deliverable specifications (what content, how many posts, timeline)
- Usage rights (how long the brand can use the content, on which platforms)
- Termination clauses (what happens if either party breaches)
- Approval process (brand reviews content before posting)

**Bilingual contracts.** ASCI requires that terms be understandable to the influencer. For Gujarati and Hindi creators, we generate an English contract (for legal precision) plus a vernacular summary (for comprehension). The Contract agent produces both.

**Limitations.** Our generated contracts are templates. They are NOT legal advice. Every contract should be reviewed by a lawyer familiar with Indian advertising law before signing. The `asci_compliant: true` flag in the output means the template includes ASCI-required sections, not that it's been legally vetted.

### Key Documentation

- ASCI Influencer Guidelines: https://asci.online/influencer-guidelines/
- ASCI Code for Self-Regulation: https://asci.online/content/asci-code-for-self-regulation/
- Ministry of Information and Broadcasting advisory: https://pib.gov.in/PressReleasePage?PRID=1960126
- ASCI disclosure checklist: https://asci.online/influencer-disclosure-checklist/

---

## Additional References

### Database Design

We use SQLite for the agents' state database. This was chosen for simplicity: single-file deployment, no server process, easy backups. The schema has tables for `brand_briefs`, `campaign_suggestions`, `conversations`, `dm_log`, and `contracts`.

### Scraper Integration

The creator data comes from a separate scraping pipeline (not part of this project). We integrate via either a shared SQLite database (`SCRAPER_DB_PATH`) or an HTTP API (`SCRAPER_API_URL`). The scraper tools abstract this away.

### Testing Strategy

Unit tests mock all external dependencies (Instagram API, scraper database, Fireworks API). Integration tests use a temporary SQLite database. The test suite runs with `pytest` and uses `pytest-mock` for mocking.
