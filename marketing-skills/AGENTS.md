# marketing-skills/ — Vendored Connector Library

Vendored from `github.com/aaron-he-zhu/aaron-marketing-skills` (see User-Agent `aaron-marketing-skills-connector/1.0` in the scripts). **Do not edit these scripts directly** — patch behavior in the first-party wrappers at `tools/connectors/*_tools.py` instead.

## WHAT IT IS

- `scripts/connectors/*.py` — 17 stdlib-only data connectors: appstore, bluesky, discourse, doh, experiment, fediverse, firecrawl, gdelt, hn, kg, ledger, pageviews, psi, rss_monitor, tavily, wayback, youtube.
- `scripts/connectors/_http.py` — shared HTTP core: SSRF-safe (rejects private/multicast/reserved IPs), retries, gzip, hard deadlines, no credential leakage across redirect origins.
- `scripts/registry-events.py` — event-sourcing runtime for the 7 truth registries (entities, creators, claims, consent, launches, channels, narrative) used by `agents/protocol/`.

Every connector is both importable and an argparse CLI that prints JSON to stdout. Python 3 stdlib only — no third-party deps. Most work keyless (Tavily, Firecrawl scrape/search, Bluesky public AppView, GDELT, HN, YouTube RSS).

## HOW IT'S INVOKED

Only via subprocess from the agent pipeline:

```
tools/connectors/<name>_tools.py  →  subprocess.run(["python", marketing-skills/scripts/connectors/<name>.py", ...])
tools/registry_tools.py           →  subprocess.run(["python", marketing-skills/scripts/registry-events.py", ...])
```

Wrappers parse JSON stdout and enforce `CONNECTOR_TIMEOUT_SECONDS` (default 30s, from `config.py`). Agents never import these scripts.

## CONVENTIONS

- **`print()` is fine here** — these are JSON-printing CLIs; the repo's loguru-only rule does not apply inside this directory.
- **Keyless-first** — prefer connector modes that need no API key; pass keys via CLI args/env only when the mode requires them.
- **Tests** — `tests/test_connector_tools.py` + `tests/test_registry_tools.py` mock `subprocess.run`; never run the real scripts in tests.
