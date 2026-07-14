#!/usr/bin/env bash
# publish-registries.sh — publish ONLY the skills that are behind on each registry.
#
# Computes the behind-set from registry-status.sh (no hardcoded queue — that is
# exactly how the retired finish-registry-publish.sh rotted), then publishes each
# stale/missing skill at its current repo version via the per-skill publishers.
# Idempotent: an already-current version returns "版本已存在" (SkillHub) or the
# "already exists" path (ClawHub) and is counted in-sync, not a failure.
# Resumable (state file) and rate-limit-aware. Dry-run by default.
#
# Usage:
#   bash scripts/publish-registries.sh                     # dry-run: list the behind-set
#   bash scripts/publish-registries.sh --live              # publish behind-set on both
#   bash scripts/publish-registries.sh --live clawhub      # one platform (clawhub|skillhub|both)
#   bash scripts/publish-registries.sh --from-json f.json  # reuse a registry-status --json snapshot
#
# ClawHub updates to existing skills are NOT hourly-capped (only brand-new skills
# are ~5/hr); SkillHub throttles bursts (发布频率过高) so we space 40s + back off
# 5 min on 429. ClawHub relicenses published skills MIT-0. Owner-run, never CI.
set -u
cd "$(cd "$(dirname "$0")/.." && pwd)"

LIVE=0; PLAT="both"; FROM=""
while [ $# -gt 0 ]; do
  case "$1" in
    --live) LIVE=1 ;;
    --from-json) shift; FROM="${1:-}" ;;
    clawhub|skillhub|both) PLAT="$1" ;;
    -h|--help) sed -n '2,20p' "$0"; exit 0 ;;
    *) echo "usage: $0 [--live] [clawhub|skillhub|both] [--from-json file]" >&2; exit 1 ;;
  esac
  shift
done

# Resume-state entries are keyed by bundle version so a state file left over
# from a previous release can never mark the next release's publishes "done".
VER="$(/usr/bin/python3 -c 'import json;print(json.load(open(".claude-plugin/plugin.json"))["version"])')"
STATE="${TMPDIR:-/tmp}/publish-registries.state"; touch "$STATE"
donep(){ grep -qxF "$1" "$STATE"; }; markp(){ echo "$1" >>"$STATE"; }

echo "==> computing behind-set (registry-status)..."
if [ -n "$FROM" ]; then JSON="$(cat "$FROM")"; else JSON="$(bash scripts/registry-status.sh --json --platform "$PLAT")"; fi
[ -n "$JSON" ] || { echo "FAIL: no status JSON" >&2; exit 1; }

behind(){ printf '%s' "$JSON" | /usr/bin/python3 -c "import sys,json;d=json.load(sys.stdin);print('\n'.join(s['skill'] for s in d['skills'] if not s['$1']))"; }
CH="$( [ "$PLAT" != skillhub ] && behind clawhub_ok )"
SH="$( [ "$PLAT" != clawhub ] && behind skillhub_ok )"
nch=$(printf '%s' "$CH" | grep -c . || true); nsh=$(printf '%s' "$SH" | grep -c . || true)
echo "    behind -> ClawHub: $nch, SkillHub: $nsh   (mode: $([ $LIVE -eq 1 ] && echo LIVE || echo dry-run))"

# Per-skill publishers upload the local working tree; a live run must ship
# exactly what GitHub serves, so require a clean tree with HEAD on origin/main
# (same guard as publish-package.sh).
if [ "$LIVE" -eq 1 ]; then
  [ -z "$(git status --porcelain)" ] || { echo "FAIL: working tree is dirty — commit/stash before a live registry publish" >&2; exit 1; }
  git fetch -q origin 2>/dev/null || true
  head_commit="$(git rev-parse HEAD)"
  if ! git merge-base --is-ancestor "$head_commit" origin/main 2>/dev/null; then
    echo "FAIL: HEAD $head_commit is not on origin/main — push first so registries match GitHub" >&2; exit 1
  fi
fi

fail=0
if [ "$PLAT" != skillhub ] && [ -n "$CH" ]; then
  echo "== ClawHub: publishing $nch behind skill(s) =="
  while read -r s; do [ -n "$s" ] || continue
    if [ "$LIVE" -eq 0 ]; then echo "  would publish (clawhub) $s"; continue; fi
    donep "ch:$VER:$s" && { echo "  skip $s (done)"; continue; }
    out=$(bash scripts/publish-clawhub.sh --skill "$s" --i-accept-mit0 2>&1); rc=$?
    if [ $rc -eq 0 ]; then echo "  OK $s"; markp "ch:$VER:$s"; else echo "  FAIL $s :: $(echo "$out"|tail -1)"; fail=1; fi
    sleep 6
  done <<< "$CH"
fi

if [ "$PLAT" != clawhub ] && [ -n "$SH" ]; then
  echo "== SkillHub: publishing $nsh behind skill(s) (40s throttle) =="
  while read -r s; do [ -n "$s" ] || continue
    if [ "$LIVE" -eq 0 ]; then echo "  would publish (skillhub) $s"; continue; fi
    donep "sh:$VER:$s" && { echo "  skip $s (done)"; continue; }
    ok=0
    for try in 1 2 3 4; do
      out=$(bash scripts/publish-skillhub.sh --live --skill "$s" 2>&1); rc=$?
      if echo "$out" | grep -qE 'Published|skillId'; then echo "  OK $s"; markp "sh:$VER:$s"; ok=1; break; fi
      if echo "$out" | grep -q '已存在'; then echo "  CURRENT $s (already at repo version)"; markp "sh:$VER:$s"; ok=1; break; fi
      if echo "$out" | grep -qiE '频率过高|429|too many|rate'; then echo "  backoff $s (try $try, 5min)"; sleep 300; continue; fi
      echo "  FAIL $s :: $(echo "$out"|tail -1)"; fail=1; break
    done
    sleep 40
  done <<< "$SH"
fi

[ "$LIVE" -eq 0 ] && echo "dry-run — nothing published. Re-run with --live." || echo "done."
exit $fail
