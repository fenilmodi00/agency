#!/usr/bin/env bash
# registry-status.sh — the distribution drift detector (owner-run, read-only).
#
# The single source of truth for "is every skill's latest version live on both
# registries, and is the bundle-plugin package current?" For each skill declared
# in .claude-plugin/plugin.json it compares:
#   repo version (VERSIONS.md)  vs  ClawHub published  vs  SkillHub published
# and reports the OpenClaw bundle-plugin package version too. Read-only — it
# never publishes; feed its --json to scripts/publish-registries.sh to act.
#
# Usage:
#   bash scripts/registry-status.sh                      # alignment table + summary
#   bash scripts/registry-status.sh --json               # machine-readable (per-skill records)
#   bash scripts/registry-status.sh --platform clawhub   # one platform only (clawhub|skillhub|both)
#
# Requires the `clawhub` and `skillhub` CLIs, logged in (owner machine). See
# docs/distribution.md. CAVEAT: SkillHub state is read via fuzzy search, so a
# "missing" can be a search-recall artifact (the item may be published but not
# surfaced). publish-registries.sh self-corrects — an idempotent publish of an
# already-current version returns "版本已存在" and is treated as in-sync.
set -u
cd "$(cd "$(dirname "$0")/.." && pwd)"

OWNER="aaron-he-zhu"
PKG_NAME="aaron-marketing"        # OpenClaw bundle-plugin package name (openclaw.plugin.json id)
JSON=0
PLAT="both"
while [ $# -gt 0 ]; do
  case "$1" in
    --json) JSON=1 ;;
    --platform) shift; PLAT="${1:-both}" ;;
    -h|--help) sed -n '2,20p' "$0"; exit 0 ;;
    *) echo "usage: $0 [--json] [--platform clawhub|skillhub|both]" >&2; exit 1 ;;
  esac
  shift
done
case "$PLAT" in clawhub|skillhub|both) ;; *) echo "bad --platform: $PLAT" >&2; exit 1 ;; esac

need(){ command -v "$1" >/dev/null 2>&1 || { echo "FAIL: '$1' CLI not found on PATH — log in on the owner machine (see docs/distribution.md)" >&2; exit 2; }; }
[ "$PLAT" = skillhub ] || need clawhub
[ "$PLAT" = clawhub ] || need skillhub

BUNDLE=$(/usr/bin/python3 -c "import json;print(json.load(open('.claude-plugin/plugin.json'))['version'])")

# skill dir -> (name, slug, repo version)
repover(){ awk -F'|' -v s=" $1 " '$2==s{gsub(/ /,"",$4);print $4;exit}' VERSIONS.md; }
slugof(){ sed -n 's/^slug: *//p' "$1/SKILL.md" | head -1; }
chver(){ [ "$PLAT" = skillhub ] && { echo "-"; return; }; clawhub inspect "$OWNER/$1" 2>/dev/null | grep -E '(^|[^a-zA-Z])Latest' | grep -oE '[0-9]+\.[0-9]+\.[0-9]+' | head -1; }
shver(){ [ "$PLAT" = clawhub ] && { echo "-"; return; }
  # Search by the exact SLUG, not the skill name: a name query (e.g. "content-writer")
  # buries an aaron-prefixed entry (aaron-content-writer) past the result cutoff and
  # reads as a false "missing". The slug query surfaces it precisely.
  skillhub search "$1" --search-limit 20 --search-timeout 8 --json 2>/dev/null | /usr/bin/python3 -c "import sys,json
try:
 d=json.load(sys.stdin); r=d if isinstance(d,list) else d.get('results',d.get('skills',[]))
 print(next((str(x.get('version','?')) for x in r if str(x.get('slug',x.get('id','')))==sys.argv[1]),''))
except Exception: print('')" "$1"; }

DIRS=$(/usr/bin/python3 -c "import json;[print(p[2:] if p.startswith('./') else p) for p in json.load(open('.claude-plugin/plugin.json'))['skills']]")

tmp="$(mktemp)"; trap 'rm -f "$tmp"' EXIT
for d in $DIRS; do
  [ -f "$d/SKILL.md" ] || continue
  name="$(basename "$d")"; slug="$(slugof "$d")"; rv="$(repover "$name")"
  ch="$(chver "$name")"; [ -z "$ch" ] && ch="MISSING"
  sh="$(shver "$slug" "$name")"; [ -z "$sh" ] && sh="MISSING"
  printf '%s\t%s\t%s\t%s\t%s\n' "$name" "$rv" "$ch" "$sh" "$slug" >> "$tmp"
done

# bundle-plugin package version
pkgv="-"
if [ "$PLAT" != skillhub ]; then
  pkgv="$(clawhub package inspect "$PKG_NAME" 2>/dev/null | grep -E '^Latest' | grep -oE '[0-9]+\.[0-9]+\.[0-9]+' | head -1)"; [ -z "$pkgv" ] && pkgv="MISSING"
fi

if [ "$JSON" -eq 1 ]; then
  BUNDLE="$BUNDLE" PLAT="$PLAT" pkgv="$pkgv" PKG_NAME="$PKG_NAME" _TMP="$tmp" /usr/bin/python3 -c "
import json,os,sys
rows=[]
for ln in open(os.environ['_TMP']):
    n,rv,ch,sh,slug=ln.rstrip('\n').split('\t')
    rows.append({'skill':n,'slug':slug,'repo':rv,'clawhub':ch,'skillhub':sh,
                 'clawhub_ok':(ch==rv),'skillhub_ok':(sh==rv)})
print(json.dumps({'bundle':os.environ['BUNDLE'],'platform':os.environ['PLAT'],
  'package':{'name':os.environ['PKG_NAME'],'clawhub':os.environ['pkgv'],'ok':os.environ['pkgv']==os.environ['BUNDLE']},
  'skills':rows},indent=2))
" _TMP="$tmp"
  exit 0
fi

# human table + summary
awk -F'\t' -v plat="$PLAT" '
function mark(v,r){return (v==r)?"ok":((v=="MISSING")?"MISS":"OLD")}
BEGIN{printf "%-30s %-8s %-9s %-9s\n","SKILL","REPO","CLAWHUB","SKILLHUB"
      printf "%-30s %-8s %-9s %-9s\n","-----","----","-------","--------"}
{
 chs=(plat=="skillhub")?"-":mark($3,$2); shs=(plat=="clawhub")?"-":mark($4,$2)
 flag=((chs=="ok"||chs=="-")&&(shs=="ok"||shs=="-"))?"":"  <-"
 printf "%-30s %-8s %-9s %-9s%s\n",$1,$2,$3" "chs,$4" "shs,flag
 tot++
 if(chs=="ok")cok++; else if(chs=="MISS")cmiss++; else if(chs!="-")cold++
 if(shs=="ok")sok++; else if(shs=="MISS")smiss++; else if(shs!="-")sold++
}
END{
 print ""
 print "== summary ("tot" skills) =="
 if(plat!="skillhub") printf "  ClawHub : %d current, %d stale, %d missing\n",cok,cold,cmiss
 if(plat!="clawhub")  printf "  SkillHub: %d current, %d stale, %d missing\n",sok,sold,smiss
}' "$tmp"

if [ "$PLAT" != skillhub ]; then
  if [ "$pkgv" = "$BUNDLE" ]; then echo "  Package : $PKG_NAME@$pkgv (current)"; else echo "  Package : $PKG_NAME@$pkgv != bundle $BUNDLE  <- publish-package.sh"; fi
fi
