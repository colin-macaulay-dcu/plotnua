#!/usr/bin/env bash
# PlotNua · is this release EXACTLY a routine Atlas statistics refresh? (founder policy, 20 Nov 2026)
# Routine Atlas statistics refreshes continue automatically; every other website release needs the founder's approval.
# Called from a copy of the release tooling taken from MAIN, twice:
#   - by release-preview.sh, to decide whether the release may skip the approval (a "no" just means: ask the founder);
#   - by the promote-atlas job, again, before anything reaches main (a "no" there is a refusal: nothing is released).
# ALL of these must hold, or the answer is "no":
#   1. the release branch was pushed by the PlotNua Release App ("plotnua-release[bot]"), in a push event. That actor is
#      set by GitHub and cannot be claimed: the App key lives only in the release-automation environment (main only),
#      so only workflows already on main can push as it. A person's (or a Claude session's) push is never routine.
#   2. the branch is release/auto/atlas-stats-<first 7 of the commit>, still at that commit;
#   3. the commit is ONE commit directly on top of the current main;
#   4. it modifies only index.html and/or atlas-stats.json (no other path, no add, delete, rename or mode change);
#   5. index.html differs from main ONLY in the six Atlas figures (three data-* attributes, three <dt> numbers), each
#      found exactly once on both sides;
#   6. atlas-stats.json differs from main ONLY in its counts and "generated" time (same keys, same wording);
#   7. the page and the record agree, every figure is a whole number, and no figure falls by more than 20%
#      (the generator's own sanity gate, MAX_DECREASE).
#   bash verify-atlas-refresh.sh <40-char sha> <branch> <actor login> <event>
# Exit 0 = routine Atlas refresh; 1 = not (with the reason). Never pushes, tags or changes anything.
set -uo pipefail
SHA="${1:-}"; BRANCH="${2:-}"; ACTOR="${3:-}"; EVENT="${4:-}"
APP_ACTOR="${ATLAS_APP_ACTOR:-plotnua-release[bot]}"
no() { echo "NOT A ROUTINE ATLAS REFRESH: $*"; exit 1; }
RUNNER_TEMP_DIR=$(mktemp -d) || { echo "NOT A ROUTINE ATLAS REFRESH: no temporary folder"; exit 1; }
trap 'rm -rf "$RUNNER_TEMP_DIR"' EXIT
[[ "$SHA" =~ ^[0-9a-f]{40}$ ]] || no "bad commit id"
[ "$ACTOR" = "$APP_ACTOR" ] || no "pushed by '$ACTOR', not by the PlotNua Release App"
[ "$EVENT" = "push" ] || no "started by '$EVENT', not by the App's push"
[ "$BRANCH" = "release/auto/atlas-stats-${SHA:0:7}" ] || no "branch '$BRANCH' is not release/auto/atlas-stats-${SHA:0:7}"
git fetch -q origin main "$BRANCH" 2>/dev/null || no "main or $BRANCH could not be read"
MAIN=$(git rev-parse origin/main) || no "main could not be read"
[ "$(git rev-parse "origin/$BRANCH" 2>/dev/null)" = "$SHA" ] || no "$BRANCH has moved since its checks ran"
[ "$(git rev-parse "$SHA^" 2>/dev/null)" = "$MAIN" ] || no "not one commit directly on top of the current main ${MAIN:0:7}"
[ "$(git rev-list --count "$MAIN..$SHA")" = "1" ] || no "not exactly one commit"
CHANGES=$(git diff --no-renames --name-status "$MAIN" "$SHA") || no "the change could not be read"
[ -n "$CHANGES" ] || no "nothing changed"
while IFS=$'\t' read -r st path; do
  [ "$st" = "M" ] || no "$path is not simply modified ($st)"
  case "$path" in index.html|atlas-stats.json) ;; *) no "it changes $path" ;; esac
done <<< "$CHANGES"
SUMMARY=$(git diff --summary "$MAIN" "$SHA") || no "the change summary could not be read"
! grep -qi 'mode change' <<< "$SUMMARY" || no "a file mode changed"
for f in index.html atlas-stats.json; do
  git show "$MAIN:$f" > "$RUNNER_TEMP_DIR/old-$f" 2>/dev/null || no "$f missing on main"
  git show "$SHA:$f"  > "$RUNNER_TEMP_DIR/new-$f" 2>/dev/null || no "$f missing in the release"
done
python3 - "$RUNNER_TEMP_DIR" <<'PY' || exit 1
import json, re, sys
d = sys.argv[1]
def no(msg):
    print("NOT A ROUTINE ATLAS REFRESH: " + msg); sys.exit(1)
read = lambda n: open("%s/%s" % (d, n), encoding="utf-8").read()
old_h, new_h, old_j, new_j = read("old-index.html"), read("new-index.html"), read("old-atlas-stats.json"), read("new-atlas-stats.json")
# the six anchors, exactly as the generator (.github/scripts/atlas_stats.py ATTRS / DTS) writes them
ANCH = {"gardenRooms": (r'data-products="(\d+)"', r'<dt id="atlasProducts">(\d+)</dt><dd>Garden Rooms</dd>'),
        "makers": (r'data-makers="(\d+)"', r'<dt id="atlasMakers">(\d+)</dt><dd>Makers researched</dd>'),
        "verifiedPrices": (r'data-prices="(\d+)"', r'<dt id="atlasPrices">(\d+)</dt><dd>Verified Prices</dd>')}
def figures(h, side):
    out, norm = {}, h
    for key, pats in ANCH.items():
        vals = []
        for p in pats:
            found = re.findall(p, h)
            if len(found) != 1:
                no("%s index.html: expected exactly one %s, found %d" % (side, p, len(found)))
            vals.append(int(found[0]))
            norm = re.sub(p, lambda m: m.group(0).replace(m.group(1), "#"), norm)
        if vals[0] != vals[1]:
            no("%s index.html: the two %s figures disagree" % (side, key))
        out[key] = vals[0]
    return out, norm
of, on = figures(old_h, "main")
nf, nn = figures(new_h, "release")
if on != nn:
    no("index.html changes something other than the six Atlas figures")
def jnorm(j, side):
    try:
        x = json.loads(j)
    except ValueError:
        no("%s atlas-stats.json is not JSON" % side)
    if not isinstance(x, dict) or not isinstance(x.get("counts"), dict):
        no("%s atlas-stats.json has no counts" % side)
    if not isinstance(x.get("generated"), str) or not re.fullmatch(r"\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ", x["generated"]):
        no("%s atlas-stats.json has no valid generated time" % side)
    counts = {}
    for k, v in x["counts"].items():
        if not isinstance(v, dict):
            no("%s atlas-stats.json: %s is not a record" % (side, k))
        for nk in ("count", "ofTotalPricingRecords"):
            if nk in v:
                if not isinstance(v[nk], int) or isinstance(v[nk], bool) or v[nk] < 0:
                    no("%s atlas-stats.json: %s.%s is not a whole number" % (side, k, nk))
                if nk == "count":
                    counts[k] = v[nk]
                v[nk] = 0
    x["generated"] = ""
    return counts, x
oc, oj = jnorm(old_j, "main")
nc, nj = jnorm(new_j, "release")
if oj != nj:
    no("atlas-stats.json changes something other than its counts and generated time")
if set(nc) != set(ANCH):
    no("atlas-stats.json does not hold exactly the three Atlas counts")
for k in ANCH:
    if nf[k] != nc[k]:
        no("index.html %s (%d) disagrees with atlas-stats.json (%d)" % (k, nf[k], nc[k]))
    if nf[k] < of[k] * 0.80:
        no("%s falls by more than 20%% (%d to %d)" % (k, of[k], nf[k]))
print("routine Atlas refresh: " + ", ".join("%s %d to %d" % (k, of[k], nf[k]) for k in ANCH))
PY
