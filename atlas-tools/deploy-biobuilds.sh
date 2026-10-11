#!/usr/bin/env bash
#
# PlotNua — deploy-biobuilds.sh
#
# Runbook steps 3 to 8, as one command instead of ten blocks to paste.
# Founder authorisation FX-BIOBUILDS-PUBLISH-20261011.
#
#   snapshot -> regenerate -> copy one file -> verify -> guards -> scope check
#
# IT DOES NOT COMMIT, STAGE OR PUSH. Those stay manual and deliberate, so
# nothing reaches GitHub that a human has not looked at. On success it prints
# the exact commit and push commands to run next.
#
# IT NEVER PRINTS THE AIRTABLE TOKEN. It checks the variable is non-empty and
# reports its length, nothing more.
#
# IT NEVER TOUCHES AN UNTRACKED FILE. No `git add .`, no reset, no clean, no
# checkout, no force. The only repository file it writes is
# additional-home-universe-v1.json, by name.
#
# Re-runnable: a second run takes a second snapshot and overwrites the staging
# directory. It will not overwrite the one previous copy of the artefact it
# keeps as a sidecar, so the last known good remains recoverable.
#
# Usage:
#   ./atlas-tools/deploy-biobuilds.sh            # the real thing
#   ./atlas-tools/deploy-biobuilds.sh --dry-run  # everything except the
#                                                # snapshot and the copy
#
set -euo pipefail

WORK="${HOME}/plotnua-atlas-work"
SNAPDIR="${WORK}/snapshot"
OUTDIR="${WORK}/out"
ARTEFACT="additional-home-universe-v1.json"
DRY_RUN=0
[ "${1:-}" = "--dry-run" ] && DRY_RUN=1

step() { printf '\n\033[1m=== %s\033[0m\n' "$*"; }
ok()   { printf '  ok    %s\n' "$*"; }
die()  { printf '\n\033[31mSTOPPED: %s\033[0m\n\n' "$*" >&2; exit 1; }

# ── 0 · we must be in the right repository, on main, with a clean tree ──────
step "0 · repository"

git rev-parse --git-dir >/dev/null 2>&1 || die "not inside a git repository."
cd "$(git rev-parse --show-toplevel)"
[ -f "$ARTEFACT" ] || die "$ARTEFACT is not here. Wrong repository?"
[ -f ".github/scripts/snapshot_atlas.py" ] || die "snapshot_atlas.py is missing."

BRANCH="$(git rev-parse --abbrev-ref HEAD)"
[ "$BRANCH" = "main" ] || die "on branch '$BRANCH', not main."
ok "repository $(pwd)"
ok "branch main at $(git rev-parse --short HEAD)"

# A dirty tracked tree before we start means we cannot later attribute a
# change to this script. Untracked files are none of our business and are
# neither listed nor touched.
DIRTY="$(git status --porcelain --untracked-files=no)"
if [ -n "$DIRTY" ]; then
  printf '%s\n' "$DIRTY" >&2
  die "tracked files are already modified. Resolve those first, so that
         afterwards the only modified file is one this script wrote."
fi
ok "no modified tracked files"

# ── 1 · the token, by length only ───────────────────────────────────────────
step "1 · AIRTABLE_TOKEN"

if [ -z "${AIRTABLE_TOKEN:-}" ]; then
  die "AIRTABLE_TOKEN is not set in this shell. Set it without writing it to
         history or to a file:
             read -rs AIRTABLE_TOKEN && export AIRTABLE_TOKEN
         then run this script again."
fi
ok "set, ${#AIRTABLE_TOKEN} characters (value not shown, and never printed)"

# ── 2 · fresh authoritative snapshot ────────────────────────────────────────
step "2 · snapshot"

mkdir -p "$SNAPDIR" "$OUTDIR"
# Outside the repository on purpose: the snapshot carries Habitation
# Classification Basis and internal research prose, and is never committed or
# deployed. snapshot_atlas.py refuses to write beside the artefacts anyway.
case "$SNAPDIR" in
  "$(pwd)"*) die "the staging directory is inside the repository. Refusing." ;;
esac
ok "staging $WORK (outside the repository, so git cannot see it)"

SNAP="${SNAPDIR}/atlas-snapshot-complete.json"
if [ "$DRY_RUN" = "1" ]; then
  [ -f "$SNAP" ] || die "--dry-run needs an existing snapshot at $SNAP."
  ok "dry run: reusing the snapshot already at $SNAP"
else
  python3 .github/scripts/snapshot_atlas.py \
    --out      "$SNAP" \
    --manifest "${SNAPDIR}/atlas-snapshot-manifest.txt" \
    || die "the snapshot failed. Nothing has been changed."
  ok "snapshot written"
fi

# The field whose absence would publish Wanderlust with no price at all.
# BB-CFG-003. The snapshot now refuses outright on the condition that
# matters, but reading the coverage line is how you SEE it rather than
# trusting that it was checked.
if grep -q "'Configuration'" "${SNAPDIR}/atlas-snapshot-manifest.txt" 2>/dev/null; then
  printf '  %s\n' "$(grep "'Configuration'" "${SNAPDIR}/atlas-snapshot-manifest.txt" | head -1 | sed 's/^ *//')"
else
  printf '  note: no Configuration line in the manifest (dry run, or an older manifest).\n'
fi

# ── 3 · regenerate ──────────────────────────────────────────────────────────
step "3 · regenerate the Additional Home universe"

python3 .github/scripts/generate_additional_home_universe.py \
  --snapshot "$SNAP" \
  --out-dir  "$OUTDIR" \
  || die "the generator failed. The repository is untouched."
ok "generated into $OUTDIR"

# The generator must write only to its --out-dir. The refresh workflow asserts
# this and so do we: if it reached into the working tree, stop.
STILL="$(git status --porcelain --untracked-files=no)"
[ -z "$STILL" ] || die "the generator modified the working tree. It must only
         write to its --out-dir. Nothing has been copied in."
ok "the generator did not touch the working tree"

[ -s "${OUTDIR}/${ARTEFACT}" ] || die "${OUTDIR}/${ARTEFACT} is missing or empty."

# ── 4 · copy exactly one file in ────────────────────────────────────────────
step "4 · copy the one production file"

if [ "$DRY_RUN" = "1" ]; then
  ok "dry run: not copying. Verifying the freshly generated file in place."
  VERIFY_TARGET="${OUTDIR}/${ARTEFACT}"
else
  # Keep the outgoing version recoverable without touching git.
  if [ ! -f "${WORK}/${ARTEFACT}.previous" ]; then
    cp "$ARTEFACT" "${WORK}/${ARTEFACT}.previous"
    ok "previous artefact kept at ${WORK}/${ARTEFACT}.previous"
  else
    ok "a .previous sidecar already exists; leaving it as the original"
  fi
  cp "${OUTDIR}/${ARTEFACT}" "$ARTEFACT"
  ok "copied ${ARTEFACT}"
  VERIFY_TARGET="$ARTEFACT"
fi

# ── 5 · the founder's facts ─────────────────────────────────────────────────
step "5 · verify Wanderlust and Serenity"

node atlas-tools/verify-biobuilds-publication.mjs --universe "$VERIFY_TARGET" \
  || die "the regenerated artefact does not carry the authorised facts.
         DO NOT DEPLOY. The failing check above names what is wrong.
         To put the previous artefact back:
             cp ${WORK}/${ARTEFACT}.previous ${ARTEFACT}"

# ── 6 · the required guards ─────────────────────────────────────────────────
step "6 · guards"

run() {
  # Label from the SCRIPT, not the interpreter: $1 is node or python3.
  printf '  %-52s' "$(basename "${2:-$1}")"
  if "$@" >/dev/null 2>&1; then printf 'ok\n'; else printf 'FAILED\n'; return 1; fi
}

GUARD_FAIL=0
run node atlas-tools/validate-image-provenance.js                  || GUARD_FAIL=1
run node atlas-tools/prove-image-provenance-capability.mjs         || GUARD_FAIL=1
run node atlas-tools/prove-image-rights-gate-capability.mjs        || GUARD_FAIL=1
run node atlas-tools/prove-supplier-publication-gate.mjs           || GUARD_FAIL=1
run node atlas-tools/prove-supplier-publication-gate-capability.mjs|| GUARD_FAIL=1
run node atlas-tools/prove-founder-exception.mjs                   || GUARD_FAIL=1
run node atlas-tools/prove-founder-exception-capability.mjs        || GUARD_FAIL=1
run node atlas-tools/prove-biobuilds-imagery.mjs                   || GUARD_FAIL=1
run node atlas-tools/prove-biobuilds-imagery-capability.mjs        || GUARD_FAIL=1
run node atlas-tools/prove-biobuilds-containment.mjs               || GUARD_FAIL=1
run node atlas-tools/prove-biobuilds-containment-capability.mjs    || GUARD_FAIL=1
run node atlas-tools/prove-results-configurations.mjs              || GUARD_FAIL=1
run node atlas-tools/prove-price-presentation-unchanged.mjs        || GUARD_FAIL=1
run node atlas-tools/prove-landmarks.mjs                           || GUARD_FAIL=1
run python3 atlas-tools/prove-price-configurations.py              || GUARD_FAIL=1
run python3 atlas-tools/prove-snapshot-configuration.py            || GUARD_FAIL=1
run python3 .github/scripts/generate_image_rights_manifest.py --check || GUARD_FAIL=1

printf '  %-52s' "validate-image-rights (scan + self-test)"
if node atlas-tools/validate-image-rights.js --scan-html . \
        --permissions image-rights-manifest.json --max-age-days 30 >/dev/null 2>&1 \
   && node atlas-tools/validate-image-rights.js --self-test >/dev/null 2>&1; then
  printf 'ok\n'
else
  printf 'FAILED\n'; GUARD_FAIL=1
fi

[ "$GUARD_FAIL" = "0" ] || die "a guard failed. Re-run the named guard on its own
         to see its output. DO NOT DEPLOY.
         To put the previous artefact back:
             cp ${WORK}/${ARTEFACT}.previous ${ARTEFACT}"

# Known and unrelated: .github/scripts/test_qualification_batch1.py has three
# pre-existing failures against the GARDEN ROOM universe, identical before and
# after this work (GR-SAN-001). It is not run here because it tests nothing
# this release changes, and a known-failing test in a deployment gate teaches
# people to ignore the gate.

# ── 7 · only the intended file changed ──────────────────────────────────────
step "7 · scope"

CHANGED="$(git status --porcelain --untracked-files=no)"
if [ "$DRY_RUN" = "1" ]; then
  [ -z "$CHANGED" ] || die "the dry run changed tracked files. It should not have."
  ok "dry run: nothing changed, as expected"
else
  EXPECTED=" M ${ARTEFACT}"
  if [ "$CHANGED" = "$EXPECTED" ]; then
    ok "exactly one modified tracked file: ${ARTEFACT}"
  else
    printf '\n  expected exactly:\n    %s\n  got:\n' "$EXPECTED"
    printf '    %s\n' "$CHANGED"
    die "the change is wider than intended. Nothing has been staged or pushed."
  fi
  printf '\n'
  git --no-pager diff --stat -- "$ARTEFACT"
fi

# ── done ────────────────────────────────────────────────────────────────────
step "READY"

if [ "$DRY_RUN" = "1" ]; then
  cat <<'DRY'
  The dry run passed. Nothing was snapshotted, copied, staged or pushed.
  Run without --dry-run to do it for real.
DRY
  exit 0
fi

cat <<NEXT
  Every check passed. Nothing is staged and nothing is pushed.

  Look at the page before you publish it. The Additional Home review harness
  is localhost-only, so this is the one place the Wanderlust card can be seen
  without walking the whole Eircode journey:

      python3 -m http.server 8080 >/dev/null 2>&1 &
      open "http://localhost:8080/your-plot.html?discovery=residential&review=additional-home"

  Three images, "BIOBUILDS model imagery", "© BIOBUILDS", both prices with
  their configuration names, including VAT, and no Serenity.

  Then publish:

      git add ${ARTEFACT}
      git --no-pager diff --cached --stat
      git commit -F atlas-tools/.biobuilds-commit-message.txt
      git push origin main

  Afterwards, runbook section 10: the live JSON check, the image HTTP check,
  and the journey walked by hand at
  https://plotnua.ie/your-plot.html?discovery=residential

  Deployment is not complete until that journey has been walked.
NEXT
