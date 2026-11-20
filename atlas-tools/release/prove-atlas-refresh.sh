#!/usr/bin/env bash
# shellcheck disable=SC2016,SC2034  # each check is a single-quoted string evaluated later by ok(): rc and the like are read there
# Proof that ONLY a routine Atlas statistics refresh can skip the founder's approval (founder policy, 20 Nov 2026).
# A throw-away local "origin" stands in for GitHub. Never touches GitHub, Pages or production.
#   bash atlas-tools/release/prove-atlas-refresh.sh
set -uo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"; VA="$HERE/verify-atlas-refresh.sh"
T=$(mktemp -d); cd "$T" || exit 1; fails=0
ok() { if eval "$2"; then echo "  PASS  $1"; else echo "  FAIL  $1"; fails=$((fails+1)); fi; }
git init -q --bare origin.git; git clone -q origin.git w 2>/dev/null; cd w || exit 1
git config user.name t; git config user.email t@t; git checkout -q -b main
page() { # products makers prices [extra]
  printf '<html><body><h1>PlotNua</h1>\n<dl class="atlas-figures" id="atlasFigures"\n    data-products="%s" data-makers="%s" data-prices="%s">\n<div><dt id="atlasProducts">%s</dt><dd>Garden Rooms</dd></div>\n<div><dt id="atlasMakers">%s</dt><dd>Makers researched</dd></div>\n<div><dt id="atlasPrices">%s</dt><dd>Verified Prices</dd></div>\n</dl>%s\n<p>Rest of the homepage</p></body></html>\n' "$1" "$2" "$3" "$1" "$2" "$3" "${4:-}"; }
stats() { # products makers prices total [generated] [note]
  printf '{\n  "source": "PlotNua Atlas Core",\n  "generated": "%s",\n  "counts": {\n    "gardenRooms": {"count": %s, "definition": "Products where Product Category = Garden Rooms"},\n    "makers": {"count": %s, "definition": "Distinct organisations"},\n    "verifiedPrices": {"count": %s, "definition": "Product Pricing where Status = Verified", "ofTotalPricingRecords": %s}\n  },\n  "note": "%s"\n}\n' "${5:-2026-11-13T13:33:56Z}" "$1" "$2" "$3" "$4" "${6:-The audit record.}"; }
page 598 97 876 > index.html; stats 598 97 876 1127 > atlas-stats.json; echo "other" > other.html
git add -A; git commit -qm base; git push -q origin main
BOT='plotnua-release[bot]'
# mk <label> : commit what is in the work tree on top of main, push it as release/auto/atlas-stats-<sha7>, set S and B
mk() { git add -A; git commit -qm "$1" >/dev/null 2>&1; S=$(git rev-parse HEAD); B="release/auto/atlas-stats-${S:0:7}"; git push -q origin "HEAD:refs/heads/$B" 2>/dev/null; }
reset_main() { git checkout -q main; git reset -q --hard origin/main; }
va() { bash "$VA" "$@" > "$T/log" 2>&1; }
yes_() { va "$@"; rc=$?; ok "ROUTINE: $LABEL" '[ $rc = 0 ]'; }
no_() { va "$@"; rc=$?; ok "NOT ROUTINE: $LABEL ($(tail -1 "$T/log" | sed 's/NOT A ROUTINE ATLAS REFRESH: //' | cut -c1-70))" '[ $rc = 1 ] && grep -q "NOT A ROUTINE ATLAS REFRESH" "$T/log"'; }

reset_main; page 598 97 881 > index.html; stats 598 97 881 1128 2026-11-14T06:00:12Z > atlas-stats.json; mk refresh
LABEL="a genuine refresh by the App (both files, figures and record agree)"; yes_ "$S" "$B" "$BOT" push
LABEL="pushed by the founder's account / a Claude session"; no_ "$S" "$B" "colin-macaulay-dcu" push
PV="$HERE/release-preview.sh"
pv() { : > "$T/out"; : > "$T/sum"; ACTOR="$1" EVENT="$2" GITHUB_STEP_SUMMARY="$T/sum" GITHUB_OUTPUT="$T/out" bash "$PV" "$S" "$B" > "$T/plog" 2>&1; }
pv "$BOT" push; rc=$?
ok "preview: the App's genuine refresh goes to promote-atlas (atlas=true, release=false: no approval asked)" '[ $rc = 0 ] && grep -qx atlas=true "$T/out" && grep -qx release=false "$T/out" && ! grep -qx release=true "$T/out"'
pv "colin-macaulay-dcu" push; rc=$?
ok "preview: the SAME commit pushed by a person is offered for the founder's approval" '[ $rc = 0 ] && grep -qx release=true "$T/out" && ! grep -qx atlas=true "$T/out"'
pv "" push; rc=$?
ok "preview: with no pusher known, it is offered for approval" '[ $rc = 0 ] && grep -qx release=true "$T/out" && ! grep -qx atlas=true "$T/out"'
LABEL="pushed by github-actions[bot]"; no_ "$S" "$B" "github-actions[bot]" push
LABEL="a dispatched gate run, not the App's push"; no_ "$S" "$B" "$BOT" workflow_dispatch
LABEL="a branch name that does not carry this commit"; no_ "$S" "release/auto/atlas-stats-0000000" "$BOT" push
LABEL="an ordinary release branch"; no_ "$S" "release/auto/homepage-${S:0:7}" "$BOT" push
SAVED_S=$S; SAVED_B=$B
reset_main; page 598 97 881 > index.html; stats 598 97 881 1128 2026-11-14T06:00:12Z > atlas-stats.json; git add -A; git commit -qm one; page 599 97 881 > index.html; stats 599 97 881 1128 2026-11-14T06:00:13Z > atlas-stats.json; mk two
LABEL="two commits on top of main"; no_ "$S" "$B" "$BOT" push
reset_main; page 598 97 881 > index.html; stats 598 97 881 1128 2026-11-14T06:00:12Z > atlas-stats.json; echo changed > other.html; mk extra
LABEL="it also changes another file"; no_ "$S" "$B" "$BOT" push
reset_main; page 598 97 881 > index.html; stats 598 97 881 1128 2026-11-14T06:00:12Z > atlas-stats.json; echo new > new.html; mk added
LABEL="it also adds a file"; no_ "$S" "$B" "$BOT" push
reset_main; page 598 97 881 > index.html; stats 598 97 881 1128 2026-11-14T06:00:12Z > atlas-stats.json; git rm -q other.html; mk deleted
LABEL="it also deletes a file"; no_ "$S" "$B" "$BOT" push
reset_main; page 598 97 881 '<script src="https://evil.example/x.js"></script>' > index.html; stats 598 97 881 1128 2026-11-14T06:00:12Z > atlas-stats.json; mk script
LABEL="index.html also gains a script beside the figures"; no_ "$S" "$B" "$BOT" push
pv "$BOT" push; rc=$?
ok "preview: an App-pushed atlas-stats branch with any other change is offered for the founder's approval" '[ $rc = 0 ] && grep -qx release=true "$T/out" && ! grep -qx atlas=true "$T/out"'
reset_main; page 598 97 881 > index.html; sed -i 's/Rest of the homepage/Different homepage text/' index.html; stats 598 97 881 1128 2026-11-14T06:00:12Z > atlas-stats.json; mk text
LABEL="index.html changes other text"; no_ "$S" "$B" "$BOT" push
reset_main; page 598 97 881 > index.html; sed -i 's/<dd>Garden Rooms</<dd>Garden Rooms (best in Ireland)</' index.html; stats 598 97 881 1128 2026-11-14T06:00:12Z > atlas-stats.json; mk label
LABEL="a figure's public label is reworded"; no_ "$S" "$B" "$BOT" push
reset_main; page 598 97 881 '<span data-prices="5">' > index.html; stats 598 97 881 1128 2026-11-14T06:00:12Z > atlas-stats.json; mk dup
LABEL="a second copy of an anchor is added"; no_ "$S" "$B" "$BOT" push
reset_main; page 598 97 881 > index.html; stats 598 97 881 1128 2026-11-14T06:00:12Z "Visit evil.example" > atlas-stats.json; mk note
LABEL="atlas-stats.json wording changes"; no_ "$S" "$B" "$BOT" push
reset_main; page 598 97 881 > index.html; stats 598 97 881 1128 2026-11-14T06:00:12Z | sed 's/"source"/"extra": "x",\n  "source"/' > atlas-stats.json; mk key
LABEL="atlas-stats.json gains a key"; no_ "$S" "$B" "$BOT" push
reset_main; page 598 97 881 > index.html; stats 598 97 880 1128 2026-11-14T06:00:12Z > atlas-stats.json; mk disagree
LABEL="the page and the record disagree"; no_ "$S" "$B" "$BOT" push
reset_main; page 598 97 600 > index.html; stats 598 97 600 1128 2026-11-14T06:00:12Z > atlas-stats.json; mk drop
LABEL="a figure falls by more than 20%"; no_ "$S" "$B" "$BOT" push
reset_main; page 598 97 881 > index.html; stats 598 97 '"881"' 1128 2026-11-14T06:00:12Z > atlas-stats.json; mk str
LABEL="a count that is not a whole number"; no_ "$S" "$B" "$BOT" push
reset_main; page 598 97 881 > index.html; stats 598 97 881 1128 "yesterday" > atlas-stats.json; mk gen
LABEL="an invalid generated time"; no_ "$S" "$B" "$BOT" push
reset_main; page 598 97 881 > index.html; stats 598 97 881 1128 2026-11-14T06:00:12Z > atlas-stats.json; chmod +x index.html; mk mode
LABEL="a file mode change"; no_ "$S" "$B" "$BOT" push
reset_main; git commit -q --allow-empty -m empty; mk empty
LABEL="an empty change"; no_ "$S" "$B" "$BOT" push
# the branch moved after its checks, and main moved on: both refused
reset_main; git commit -q --allow-empty -m other; git push -q origin "+HEAD:refs/heads/$SAVED_B" 2>/dev/null; reset_main
LABEL="the release branch was moved to another commit after its checks"; no_ "$SAVED_S" "$SAVED_B" "$BOT" push
git checkout -q main; echo publisher > gallery.html; git add -A; git commit -qm "a publisher moved main"; git push -q origin main
LABEL="main moved on since the refresh was made"; no_ "$SAVED_S" "$SAVED_B" "$BOT" push
LABEL="a bad commit id"; no_ "${SAVED_S:0:7}" "$SAVED_B" "$BOT" push
echo; echo "ATLAS REFRESH PROOF · $([ $fails = 0 ] && echo OK || echo FAIL) · $fails failed"; rm -rf "$T"; exit $fails
