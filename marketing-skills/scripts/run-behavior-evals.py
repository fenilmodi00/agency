#!/usr/bin/env python3
"""Run offline conformance suites and, optionally, a semantic host adapter.

The default path is deterministic and network-free. ``--adapter-command`` is an
explicit extension point for a host/model harness: cases are sent as NDJSON on
stdin and one schema-valid result per case must be returned as NDJSON on stdout.
Adapter scores are never stored as golden baselines.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import shlex
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
SUITES_PATH = ROOT / "evals" / "deterministic-suites.json"
CASE_LINE = re.compile(r"^\s*-?\s*(\{.*\})\s*$")
ID_RE = re.compile(r'(?:^|[{,])\s*"?id"?\s*:\s*"?([A-Za-z0-9._-]+)"?')
TARGET_RE = re.compile(r'(?:^|[{,])\s*"?target_skill"?\s*:\s*"?([A-Za-z0-9_-]+)"?')
RESULT_KEYS = {
    "id", "passed", "evidence", "observed_assertions", "failure_modes_seen",
    "adapter_version",
}


class BehaviorEvalError(ValueError):
    pass


def load_json(path):
    try:
        with path.open(encoding="utf-8") as handle:
            return json.load(handle)
    except (OSError, ValueError) as exc:
        raise BehaviorEvalError("cannot load %s: %s" % (path, exc)) from exc


def validate_suite_manifest(manifest):
    if set(manifest) != {"schema_version", "description", "suites"}:
        raise BehaviorEvalError("deterministic suite manifest has unknown or missing keys")
    if manifest["schema_version"] != "1.0" or not isinstance(manifest["suites"], list):
        raise BehaviorEvalError("invalid deterministic suite manifest")
    seen = set()
    for suite in manifest["suites"]:
        if set(suite) != {"id", "command", "timeout_seconds"}:
            raise BehaviorEvalError("suite entries require exactly id, command, timeout_seconds")
        if suite["id"] in seen:
            raise BehaviorEvalError("duplicate suite id: %s" % suite["id"])
        seen.add(suite["id"])
        if not isinstance(suite["command"], list) or not suite["command"] or not all(
                isinstance(part, str) and part for part in suite["command"]):
            raise BehaviorEvalError("suite %s command must be a non-empty argument array" % suite["id"])
        timeout = suite["timeout_seconds"]
        if not isinstance(timeout, int) or isinstance(timeout, bool) or not 1 <= timeout <= 600:
            raise BehaviorEvalError("suite %s timeout must be 1..600 seconds" % suite["id"])


def expand_command(parts):
    replacements = {"{python}": sys.executable, "{root}": str(ROOT)}
    return [replacements.get(part, part) for part in parts]


def run_deterministic(selected):
    manifest = load_json(SUITES_PATH)
    validate_suite_manifest(manifest)
    suites = manifest["suites"]
    if selected:
        unknown = sorted(set(selected) - {suite["id"] for suite in suites})
        if unknown:
            raise BehaviorEvalError("unknown deterministic suite(s): %s" % ", ".join(unknown))
        suites = [suite for suite in suites if suite["id"] in selected]
    failures = []
    for suite in suites:
        command = expand_command(suite["command"])
        print("RUN   %s" % suite["id"])
        try:
            result = subprocess.run(
                command,
                cwd=ROOT,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                timeout=suite["timeout_seconds"],
                check=False,
            )
        except (OSError, subprocess.TimeoutExpired) as exc:
            failures.append("%s: %s" % (suite["id"], exc))
            print("FAIL  " + failures[-1])
            continue
        if result.returncode:
            tail = "\n".join(result.stdout.splitlines()[-30:])
            failures.append("%s exited %d\n%s" % (suite["id"], result.returncode, tail))
            print("FAIL  %s exited %d" % (suite["id"], result.returncode))
        else:
            summary = next((line for line in reversed(result.stdout.splitlines()) if line.strip()), "passed")
            print("PASS  %s: %s" % (suite["id"], summary.strip()))
    return failures


def discover_semantic_cases(filters):
    cases = []
    for path in sorted((ROOT / "evals").glob("*/cases.md")):
        if " 2" in path.name:
            continue
        for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            matched = CASE_LINE.match(line)
            if not matched:
                continue
            raw = matched.group(1)
            case_id = ID_RE.search(raw)
            target = TARGET_RE.search(raw)
            if not case_id or not target:
                continue
            if filters and not any(value in {case_id.group(1), target.group(1)} for value in filters):
                continue
            cases.append({
                "protocol_version": "1.0",
                "id": case_id.group(1),
                "target_skill": target.group(1),
                "case_source": str(path.relative_to(ROOT)),
                "case_line": line_number,
                "skill_path": find_skill_path(target.group(1)),
                "raw_case": raw,
            })
    ids = [case["id"] for case in cases]
    duplicates = sorted({case_id for case_id in ids if ids.count(case_id) > 1})
    if duplicates:
        raise BehaviorEvalError("semantic case IDs are not unique: %s" % ", ".join(duplicates))
    if filters and not cases:
        raise BehaviorEvalError("no semantic cases matched --case filters")
    return cases


def find_skill_path(slug):
    matches = list(ROOT.glob("*/*/%s/SKILL.md" % slug)) + list(ROOT.glob("protocol/%s/SKILL.md" % slug))
    if len(matches) != 1:
        raise BehaviorEvalError("target skill %s resolves to %d paths" % (slug, len(matches)))
    return str(matches[0].relative_to(ROOT))


def validate_adapter_result(value):
    if not isinstance(value, dict):
        raise BehaviorEvalError("adapter result must be an object")
    if set(value) - RESULT_KEYS:
        raise BehaviorEvalError("adapter result has unknown keys: %s" % sorted(set(value) - RESULT_KEYS))
    if not isinstance(value.get("id"), str) or not value["id"]:
        raise BehaviorEvalError("adapter result id is required")
    if not isinstance(value.get("passed"), bool):
        raise BehaviorEvalError("adapter result passed must be boolean")
    if not isinstance(value.get("evidence"), str) or not value["evidence"].strip():
        raise BehaviorEvalError("adapter result evidence is required")
    for key in ("observed_assertions", "failure_modes_seen"):
        if key in value and (not isinstance(value[key], list) or not all(
                isinstance(item, str) for item in value[key])):
            raise BehaviorEvalError("adapter result %s must be an array of strings" % key)


def run_adapter(command_text, filters, timeout):
    try:
        command = shlex.split(command_text)
    except ValueError as exc:
        raise BehaviorEvalError("cannot parse --adapter-command: %s" % exc) from exc
    if not command:
        raise BehaviorEvalError("--adapter-command cannot be empty")
    cases = discover_semantic_cases(filters)
    payload = "".join(json.dumps(case, ensure_ascii=False) + "\n" for case in cases)
    print("RUN   semantic-adapter: %d case(s)" % len(cases))
    try:
        result = subprocess.run(
            command,
            cwd=ROOT,
            input=payload,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise BehaviorEvalError("semantic adapter failed: %s" % exc) from exc
    if result.returncode:
        raise BehaviorEvalError(
            "semantic adapter exited %d: %s" % (result.returncode, result.stderr[-2000:])
        )
    outputs = []
    for line_number, line in enumerate(result.stdout.splitlines(), 1):
        if not line.strip():
            continue
        try:
            value = json.loads(line)
        except ValueError as exc:
            raise BehaviorEvalError("adapter stdout line %d is not JSON" % line_number) from exc
        validate_adapter_result(value)
        outputs.append(value)
    expected = {case["id"] for case in cases}
    returned = [value["id"] for value in outputs]
    duplicates = sorted({case_id for case_id in returned if returned.count(case_id) > 1})
    if duplicates:
        raise BehaviorEvalError("adapter returned duplicate IDs: %s" % ", ".join(duplicates))
    missing = sorted(expected - set(returned))
    unknown = sorted(set(returned) - expected)
    if missing or unknown:
        raise BehaviorEvalError("adapter coverage mismatch; missing=%s unknown=%s" % (missing, unknown))
    failed = [value for value in outputs if not value["passed"]]
    for value in failed:
        print("FAIL  %s: %s" % (value["id"], value["evidence"]))
    if failed:
        return ["semantic adapter failed %d/%d cases" % (len(failed), len(outputs))]
    print("PASS  semantic-adapter: %d/%d" % (len(outputs), len(cases)))
    return []


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--suite", action="append", default=[], help="Run only this deterministic suite ID.")
    parser.add_argument("--adapter-command", help="Optional NDJSON semantic-eval adapter command.")
    parser.add_argument("--adapter-only", action="store_true", help="Skip deterministic suites.")
    parser.add_argument("--case", action="append", default=[], help="Adapter case ID or target-skill filter.")
    parser.add_argument("--adapter-timeout", type=int, default=1800)
    args = parser.parse_args(argv)
    if args.adapter_only and not args.adapter_command:
        parser.error("--adapter-only requires --adapter-command")
    if not 1 <= args.adapter_timeout <= 7200:
        parser.error("--adapter-timeout must be 1..7200 seconds")
    failures = []
    try:
        if not args.adapter_only:
            failures.extend(run_deterministic(set(args.suite)))
        if args.adapter_command:
            failures.extend(run_adapter(args.adapter_command, set(args.case), args.adapter_timeout))
    except BehaviorEvalError as exc:
        failures.append(str(exc))
    if failures:
        print("\nBEHAVIOR CONFORMANCE FAILED: %d issue(s)" % len(failures))
        for failure in failures:
            print("- " + failure)
        return 1
    print("\nBehavior conformance passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
