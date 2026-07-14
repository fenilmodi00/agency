# Marketing Skills — Influencer + Protocol (merged)

Merged from [`aaron-marketing-skills`](https://github.com/aaron-he-zhu/aaron-marketing-skills) (v18.0.0, Apache-2.0)
into this workspace on 2026-07-14.

## What was merged

Scope: **Influencer marketing (16 skills)** + **Protocol layer (8 skills)**, preserving the
original folder tree so cross-skill relative links, shared `references/`, `scripts/`, and
`memory/` templates all resolve.

| Layer | Skills | Path |
|---|---|---|
| Influencer · scout | `audience-mapper`, `trend-spotter`, `influencer-discovery`, `fit-scorer` | `influencer/scout/` |
| Influencer · target | `competitor-tracker`, `campaign-planner`, `brief-generator`, `budget-optimizer` | `influencer/target/` |
| Influencer · activate | `outreach-manager`, `creator-content-auditor`, `contract-helper`, `content-amplifier` | `influencer/activate/` |
| Influencer · report | `landing-optimizer`, `performance-analyzer`, `roi-calculator`, `report-generator` | `influencer/report/` |
| Protocol (registries) | `entity-registry`, `creator-registry`, `offer-claims-registry`, `consent-registry`, `launch-registry`, `channel-registry`, `narrative-registry`, `memory-management` | `protocol/` |

Shared dependencies kept: `references/` (skill-contract, state-model, benchmarks),
`scripts/` (connectors incl. keyless YouTube), `memory/` (runtime templates), `CONNECTORS.md`, `LICENSE`.

## How this maps to the existing campaign (D:\0)

The workspace already runs an influencer campaign (`AGENTS.md`, `crew.py`, `main.py`).
The merged skills are a richer, more detailed playbook for the same funnel:

| Existing agent (AGENTS.md) | Closest merged skill(s) |
|---|---|
| Discovery | `influencer/scout/influencer-discovery`, `fit-scorer` |
| Proposal | `influencer/target/campaign-planner`, `brief-generator` |
| Outreach | `influencer/activate/outreach-manager` |
| Negotiator | `influencer/activate/outreach-manager` (negotiation) + `contract-helper` |
| Contract | `influencer/activate/contract-helper` |
| (reporting) | `influencer/report/*` |
| (shared state) | `protocol/creator-registry`, `protocol/consent-registry`, `protocol/memory-management` |

The `protocol/` registries are the canonical "source of truth" layer the skills write to via
`operation: propose` requests — wire them to the existing `db/` (SQLite at `AGENTS_DB_PATH`)
if you want the campaign's state to back the registries.

## Known dangling references (expected)

9 files contain 11 prose pointers to disciplines that were **not** merged (launch, social,
paid `ad`, `seo-geo`). They are descriptive "cross-discipline" notes, not load-bearing for
these skills. Examples: `report-generator` → `seo-geo/tune/content-quality-auditor`;
`roi-calculator` → `ad/scale/paid-measurement-loop`. Left as-is to avoid shotgun edits;
merge those families later if you want the links live.

## Usage

Each skill is a `SKILL.md` readable directly. Frontmatter uses `name` / `description` /
`when_to_use` — compatible with OpenCode/Claude-Code skill hosts. To expose them as OpenCode
skills, point your skill loader at `D:\0\marketing-skills\influencer\**\SKILL.md` and
`D:\0\marketing-skills\protocol\**\SKILL.md`.
