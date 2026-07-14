#!/usr/bin/env python3
"""Generate/check immutable standalone auditor runtime bundles.

Each auditor ships one local ``references/auditor-runtime.md`` assembled from
the typed framework slice and the exact repository sources declared in
``references/system-catalog.json``. This removes mutable-branch fallbacks while
keeping the root references authoritative in repository mode.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import tempfile
import sys


ROOT = Path(__file__).resolve().parents[1]
SYSTEM_CATALOG = ROOT / "references" / "system-catalog.json"
FRAMEWORK_CATALOG = ROOT / "references" / "framework-catalog.json"
OUTPUT_NAME = "auditor-runtime.md"


class GenerationError(ValueError):
    pass


def load_json(path):
    try:
        with path.open(encoding="utf-8") as handle:
            return json.load(handle)
    except (OSError, ValueError) as exc:
        raise GenerationError("cannot load %s: %s" % (path, exc)) from exc


def safe_source(relative):
    path = (ROOT / relative).resolve()
    try:
        path.relative_to(ROOT.resolve())
    except ValueError as exc:
        raise GenerationError("runtime source escapes repository: %s" % relative) from exc
    if not path.is_file():
        raise GenerationError("runtime source is missing: %s" % relative)
    return path


def build_bundle(auditor, framework_catalog):
    framework_name = auditor["framework"]
    framework = framework_catalog.get("frameworks", {}).get(framework_name)
    if framework is None:
        raise GenerationError("unknown framework for %s: %s" % (auditor["skill"], framework_name))
    source_paths = [(relative, safe_source(relative)) for relative in auditor["runtime_sources"]]
    snapshot = {
        "catalog_version": framework_catalog["catalog_version"],
        "semantics": framework_catalog["semantics"],
        "frameworks": {framework_name: framework},
    }
    snapshot_text = json.dumps(snapshot, indent=2, ensure_ascii=False, sort_keys=True) + "\n"
    digest = hashlib.sha256()
    digest.update(snapshot_text.encode("utf-8"))
    for relative, path in source_paths:
        digest.update(relative.encode("utf-8"))
        digest.update(b"\0")
        digest.update(path.read_bytes())
    lines = [
        "<!-- GENERATED FILE: run `python3 scripts/generate-auditor-runtime.py --write`; do not edit. -->",
        "",
        "# Standalone Auditor Runtime",
        "",
        "- **Runtime version:** 3.0.0",
        "- **Catalog version:** %s" % framework_catalog["catalog_version"],
        "- **Framework:** %s" % framework_name,
        "- **Auditor:** %s" % auditor["skill"],
        "- **Source digest:** `sha256:%s`" % digest.hexdigest(),
        "",
        "This immutable bundle is the fail-closed standalone fallback for this auditor. It contains the exact typed framework slice needed to collect observations without inventing rules. Repository/plugin installs use the root policy, schemas, and deterministic scorer. A standalone one-folder install must not fetch mutable sources, compute a score, claim a gate verdict, or persist an audit artifact.",
        "",
        "## Typed Framework Snapshot",
        "",
        "```json",
        snapshot_text.rstrip("\n"),
        "```",
    ]
    lines.extend([
        "",
        "## Standalone Execution Policy",
        "",
        "1. Select exactly one declared profile from the typed snapshot and record it with the catalog version and source digest above.",
        "2. Collect one state per applicable item using the run-schema vocabulary: `pass`, `partial`, `fail`, `na`, or `unknown` — the same states the root scorer replays later. Every non-unknown state needs evidence; never convert missing evidence into a pass.",
        "3. Record veto observations by their qualified framework item IDs, but do not calculate dimension, raw, capped, or final scores without the root deterministic scorer.",
        "4. Return `status: NEEDS_INPUT` or `status: BLOCKED` with `verdict: UNDECIDED`, `score_state: NOT_SCORED`, and `score_confidence: not_scored`. Clearly identify the unavailable root runtime as the reason.",
        "5. Do not write under `memory/audits/`, mutate registries, or claim a publish/ship decision. Offer the observation set for later execution in a full plugin or repository install.",
        "6. Do not search parent directories, accept an unverified runtime root, download repository files, or hand-calculate a substitute score.",
        "",
        "The source digest binds this compact fallback to the authoritative runbook, scoring semantics, framework benchmark, run schema, and artifact schema without copying those maintenance sources into every standalone bundle.",
    ])
    lines.extend(["", "---", "", "End of generated standalone runtime.", ""])
    return "\n".join(lines).encode("utf-8")


def output_path(auditor):
    skill_dir = (ROOT / auditor["path"]).resolve()
    try:
        skill_dir.relative_to(ROOT.resolve())
    except ValueError as exc:
        raise GenerationError("auditor path escapes repository") from exc
    if not (skill_dir / "SKILL.md").is_file():
        raise GenerationError("auditor skill path is invalid: %s" % auditor["path"])
    return skill_dir / "references" / OUTPUT_NAME


def atomic_write(path, content):
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix=".%s." % path.name, dir=str(path.parent))
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_name, path)
    finally:
        if os.path.exists(temp_name):
            os.unlink(temp_name)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", action="store_true", help="Regenerate all eight bundles.")
    mode.add_argument("--check", action="store_true", help="Fail if a bundle is missing or stale.")
    args = parser.parse_args(argv)
    try:
        system = load_json(SYSTEM_CATALOG)
        frameworks = load_json(FRAMEWORK_CATALOG)
        auditors = system.get("auditors", [])
        if len(auditors) != system.get("counts", {}).get("auditors"):
            raise GenerationError("system catalog auditor count is inconsistent")
        stale = []
        for auditor in auditors:
            path = output_path(auditor)
            expected = build_bundle(auditor, frameworks)
            if args.write:
                atomic_write(path, expected)
                print("wrote %s" % path.relative_to(ROOT))
            elif not path.is_file() or path.read_bytes() != expected:
                stale.append(str(path.relative_to(ROOT)))
        if stale:
            raise GenerationError(
                "standalone auditor runtime bundle(s) missing/stale: %s; run with --write"
                % ", ".join(stale)
            )
    except GenerationError as exc:
        print("error: %s" % exc, file=sys.stderr)
        return 1
    print("standalone auditor runtime bundles %s (%d/%d)" % ("generated" if args.write else "current", len(auditors), len(auditors)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
