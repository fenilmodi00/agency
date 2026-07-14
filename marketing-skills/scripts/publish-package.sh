#!/usr/bin/env bash
# publish-package.sh — publish the whole plugin to ClawHub as an OpenClaw
# bundle-plugin package.
#
# Default source is the current pushed HEAD via GitHub (owner/repo@sha),
# NOT the local folder: `clawhub package publish .` ignores .gitignore and would
# bundle .git, local settings, and any stray worktree. A GitHub source is a
# git-archive of committed files only. Name/version/display come from
# openclaw.plugin.json + .claude-plugin/plugin.json. Dry-run by default.
#
# --from-build publishes the minimal plugin profile built by
# scripts/build-distribution.py (references/distribution-files.json closure —
# no docs/evals/tests) from a fresh temp directory instead. Use it when the
# full git archive exceeds ClawHub's upload limit (first hit at v17.0.0:
# 413 Request Entity Too Large). The same committed-HEAD guardrails apply, so
# the built profile equals what GitHub serves.
#
# Usage:
#   bash scripts/publish-package.sh                     # dry-run: show the file set + metadata
#   bash scripts/publish-package.sh --live              # publish from GitHub source
#   bash scripts/publish-package.sh --from-build --live # publish the built minimal profile
#
# Requires: openclaw.plugin.json committed at HEAD, HEAD pushed to origin, and the
# `clawhub` CLI logged in. Owner-run, never CI. See docs/distribution.md.
set -u
cd "$(cd "$(dirname "$0")/.." && pwd)"

LIVE=0; FROM_BUILD=0
while [ $# -gt 0 ]; do
  case "$1" in
    --live) LIVE=1 ;;
    --dry-run) LIVE=0 ;;
    --from-build) FROM_BUILD=1 ;;
    -h|--help) sed -n '2,24p' "$0"; exit 0 ;;
    *) echo "usage: $0 [--from-build] [--live]" >&2; exit 1 ;;
  esac
  shift
done

command -v clawhub >/dev/null 2>&1 || { echo "FAIL: clawhub CLI not found/logged in" >&2; exit 2; }
[ -f openclaw.plugin.json ] || { echo "FAIL: openclaw.plugin.json missing at repo root" >&2; exit 1; }

REPO_SLUG=$(git remote get-url origin 2>/dev/null | sed -E 's#(git@[^:]+:|https?://[^/]+/)##; s#\.git$##')
OWNER="${REPO_SLUG%%/*}"
COMMIT=$(git rev-parse HEAD)
VER=$(/usr/bin/python3 -c "import json;print(json.load(open('.claude-plugin/plugin.json'))['version'])")
NAME=$(/usr/bin/python3 -c "import json;print(json.load(open('openclaw.plugin.json'))['id'])")
DISPLAY=$(/usr/bin/python3 -c "import json;d=json.load(open('openclaw.plugin.json'));print(d.get('name',d['id']))")

# guardrails: manifest committed at HEAD, HEAD pushed, manifest version == bundle
git cat-file -e "HEAD:openclaw.plugin.json" 2>/dev/null || { echo "FAIL: openclaw.plugin.json is not committed at HEAD $COMMIT — commit it first" >&2; exit 1; }
git fetch -q origin 2>/dev/null || true
if ! git merge-base --is-ancestor "$COMMIT" origin/main 2>/dev/null; then
  echo "FAIL: HEAD $COMMIT is not on origin/main — push it first (GitHub source publish needs it live)" >&2; exit 1
fi
mv="$(/usr/bin/python3 -c "import json;print(json.load(open('openclaw.plugin.json'))['version'])")"
[ "$mv" = "$VER" ] || { echo "FAIL: openclaw.plugin.json version $mv != bundle $VER" >&2; exit 1; }

SOURCE="$REPO_SLUG@$COMMIT"
BUILD_DIR=""
if [ "$FROM_BUILD" -eq 1 ]; then
  [ -z "$(git status --porcelain)" ] || { echo "FAIL: working tree is dirty — the built profile must equal the pushed HEAD" >&2; exit 1; }
  BUILD_DIR="$(mktemp -d "${TMPDIR:-/tmp}/aaron-plugin-build.XXXXXX")"
  trap '[ -n "$BUILD_DIR" ] && rm -rf "$BUILD_DIR"' EXIT
  /usr/bin/python3 scripts/build-distribution.py --plugin --output "$BUILD_DIR/pkg" \
    || { echo "FAIL: build-distribution.py --plugin failed" >&2; exit 1; }
  SOURCE="$BUILD_DIR/pkg"
fi

echo "Package : $NAME@$VER  (family bundle-plugin, owner $OWNER)"
if [ "$FROM_BUILD" -eq 1 ]; then
  echo "Source  : built minimal profile from HEAD $COMMIT ($SOURCE)"
else
  echo "Source  : github:$SOURCE"
fi
echo "Mode    : $([ $LIVE -eq 1 ] && echo LIVE || echo dry-run)"

cmd=(clawhub package publish "$SOURCE"
     --family bundle-plugin --name "$NAME" --display-name "$DISPLAY"
     --owner "$OWNER" --version "$VER"
     --source-repo "$REPO_SLUG" --source-commit "$COMMIT"
     --changelog "aaron-marketing bundle-plugin @ $VER — 120 skills + 8 commands, seven disciplines + protocol layer.")
[ "$LIVE" -eq 0 ] && cmd+=(--dry-run)

"${cmd[@]}"
