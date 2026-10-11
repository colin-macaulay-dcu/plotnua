# BIOBUILDS · DEPLOYMENT RUNBOOK

Founder authorisation **FX-BIOBUILDS-PUBLISH-20261011**. Compare imagery is
unchanged for this release, by founder decision, 11 October 2026.

Run on the founder's Mac, which holds the authoritative Airtable environment.

**AMENDED 11 October 2026, after the code was pushed.** When this runbook was
written, twelve commits were waiting on `main`. They have since been pushed:
`origin/main` is now `0af94f3`, and `git rev-list --count origin/main..HEAD`
reads **0**, not 12. So the *code* for this release — the publication gate,
the imagery pipeline, the `Configuration` fix, the verifier — is already live.
The **data** is not: the deployed `additional-home-universe-v1.json` is still
the 22 September artefact, carrying the superseded €112,700 and €208,500 and
no imagery, which was confirmed by fetching it from plotnua.ie.

What remains is therefore only: snapshot, regenerate, verify, commit that one
file, push, and check live.

## THE SHORT PATH

Sections 3 to 8 are now one reviewed, tested script. Prefer it — it makes the
same checks in the same order and cannot skip one by mis-paste:

```bash
cd ~/Documents/PlotNua/04\ Deploy/plotnua-github
read -rs AIRTABLE_TOKEN && export AIRTABLE_TOKEN     # does not echo, no history
./atlas-tools/deploy-biobuilds.sh
```

It stops at the first failure, never prints the token, writes only
`additional-home-universe-v1.json`, touches no untracked file, and does not
stage, commit or push — it prints those commands for you to run. Proved to
stop on a missing token, a dirty tracked tree, and an artefact whose area is
wrong; proved to pass on good data and leave the tree clean.

The sections below remain as the manual equivalent, and as the explanation of
what the script is doing and why.

**Every block stops on the first failure.** Nothing here uses `git add .`,
`git reset`, `git clean` or `git push --force`, and nothing prints the
Airtable token.

---

## 0 · THE ONE THING THAT WILL CATCH YOU OUT

The snapshot must be written **outside the repository**. `snapshot_atlas.py`
refuses to write into a directory holding `additional-home-universe-v1.json`,
and the generator refuses a `--out-dir` holding `your-plot.html` — so both
write to a staging directory and exactly one file is copied in afterwards.
That is the pattern `atlas-match-universe-refresh.yml` already uses; this
runbook follows it rather than inventing a second one.

The snapshot carries Habitation Classification Basis and internal research
prose. **It is never committed and never deployed.** `~/plotnua-atlas-work/`
sits outside the repository, so git cannot see it.

---

## 1 · ENTER THE REPOSITORY AND READ THE TREE

```bash
cd ~/Documents/PlotNua/04\ Deploy/plotnua-github || exit 1
git rev-parse --abbrev-ref HEAD
git fetch origin
echo "--- unpushed commits ---"
git rev-list --count origin/main..HEAD
git log --oneline origin/main..HEAD
echo "--- working tree (tracked files only) ---"
git status --porcelain --untracked-files=no
```

Expect the branch `main`, **0** unpushed commits with `0af94f3` at the top
(the twelve were pushed on 11 October), and **no modified tracked files**. If
`git status` lists anything, stop and read it before going further — the
regeneration is about to write one file and you want to know what was already
dirty.

Untracked files are not listed by `--untracked-files=no` and are not touched
by anything in this runbook.

---

## 2 · CONFIRM THE TOKEN WITHOUT PRINTING IT

```bash
if [ -n "${AIRTABLE_TOKEN:-}" ]; then
  echo "AIRTABLE_TOKEN is set (${#AIRTABLE_TOKEN} characters). Value not shown."
else
  echo "AIRTABLE_TOKEN is NOT set. Export it in this shell, then re-run."
fi
```

Only the character count is printed. If it is not set, export it in this
shell — not in a file, and not in a command that gets written to history:

```bash
read -rs AIRTABLE_TOKEN && export AIRTABLE_TOKEN
```

`read -rs` does not echo and does not enter shell history.

---

## 3 · FRESH AUTHORITATIVE SNAPSHOT

```bash
mkdir -p ~/plotnua-atlas-work/snapshot ~/plotnua-atlas-work/out
python3 .github/scripts/snapshot_atlas.py \
  --out      ~/plotnua-atlas-work/snapshot/atlas-snapshot-complete.json \
  --manifest ~/plotnua-atlas-work/snapshot/atlas-snapshot-manifest.txt || exit 1
```

It prints a field-coverage manifest and fails closed if a required governed
field is missing or a multi-priced Additional Home product has no
configuration labels. It prints no Basis prose and never echoes the token.

**Read one line of the manifest before continuing:**

```bash
grep -i "'Configuration'" ~/plotnua-atlas-work/snapshot/atlas-snapshot-manifest.txt
```

A non-zero coverage count is what makes both BIOBUILDS prices publishable.
Zero means the field was renamed in Airtable — stop, and say so.

---

## 4 · REGENERATE THE ADDITIONAL HOME UNIVERSE

```bash
python3 .github/scripts/generate_additional_home_universe.py \
  --snapshot ~/plotnua-atlas-work/snapshot/atlas-snapshot-complete.json \
  --out-dir  ~/plotnua-atlas-work/out || exit 1

git status --porcelain --untracked-files=no
```

The generator writes only to `--out-dir`. That `git status` must still be
empty: if the generator touched the working tree, stop.

```bash
cp ~/plotnua-atlas-work/out/additional-home-universe-v1.json \
   additional-home-universe-v1.json || exit 1
git --no-pager diff --stat -- additional-home-universe-v1.json
```

Exactly one file changed. The signal audit stays in the staging directory —
it is internal and is not deployed.

---

## 5 · VERIFY WANDERLUST AND SERENITY

```bash
node atlas-tools/verify-biobuilds-publication.mjs || exit 1
```

Twenty checks, each naming the fact it is asserting: Wanderlust PUBLISHABLE,
Class 3A CANDIDATE, 35.54 m² verified internal, €105,000 Exterior Finished and
€163,000 Turnkey both labelled, VAT-inclusive, three authorised images with
`© BIOBUILDS`, the link back and a medium-neutral caption; Serenity
`NOT_A_CANDIDATE · no-usable-area`; no superseded figure; no withheld asset;
no held product carrying imagery.

**If it fails, stop and do not deploy.** It prints which fact is wrong.

Its own capability proof, if you want to see that the checks can fail:

```bash
node atlas-tools/verify-biobuilds-publication.mjs --self-test
```

---

## 6 · THE REQUIRED GUARDS

```bash
set -e
node atlas-tools/validate-image-provenance.js
node atlas-tools/prove-image-provenance-capability.mjs
node atlas-tools/prove-image-rights-gate-capability.mjs
node atlas-tools/validate-image-rights.js --scan-html . \
     --permissions image-rights-manifest.json --max-age-days 30
node atlas-tools/validate-image-rights.js --self-test
python3 .github/scripts/generate_image_rights_manifest.py --check
node atlas-tools/prove-supplier-publication-gate.mjs
node atlas-tools/prove-supplier-publication-gate-capability.mjs
node atlas-tools/prove-founder-exception.mjs
node atlas-tools/prove-founder-exception-capability.mjs
node atlas-tools/prove-biobuilds-imagery.mjs
node atlas-tools/prove-biobuilds-imagery-capability.mjs
node atlas-tools/prove-biobuilds-containment.mjs
node atlas-tools/prove-biobuilds-containment-capability.mjs
node atlas-tools/prove-results-configurations.mjs
node atlas-tools/prove-price-presentation-unchanged.mjs
node atlas-tools/prove-landmarks.mjs
python3 atlas-tools/prove-price-configurations.py
python3 atlas-tools/prove-snapshot-configuration.py
set +e
```

`set -e` stops the block at the first non-zero exit.

**Known and unrelated:** `.github/scripts/test_qualification_batch1.py` has
three pre-existing failures against the *Garden Room* universe, identical
before and after this work. Recorded as GR-SAN-001. It is not in this list
because it does not test anything this release changes.

---

## 7 · CONFIRM ONLY THE INTENDED FILE CHANGED

```bash
echo "--- modified tracked files ---"
git status --porcelain --untracked-files=no
echo "--- untracked (expect .bak sidecars and staging only) ---"
git status --porcelain --untracked-files=all | grep '^??'
```

The first list must contain **exactly one line**:
`M additional-home-universe-v1.json`. Anything else, stop.

The untracked list will show `.bak` sidecars from earlier builders. Leave them
alone — they are not staged, not committed and not deployed.

---

## 8 · SEE IT RENDER BEFORE YOU PUSH

The Additional Home review harness is **localhost-only**: it checks hostname,
`http:` and the parameter, and does nothing at all on the live site. So this
is the one place you can see the Wanderlust card without completing the
Eircode journey.

```bash
python3 -m http.server 8080 >/dev/null 2>&1 &
echo "server pid $! — stop it with: kill $!"
open "http://localhost:8080/your-plot.html?discovery=residential&review=additional-home"
```

Look for: Wanderlust with three images, `BIOBUILDS model imagery`,
`© BIOBUILDS`, a working link to biobuilds.com, both prices with their
configuration names, `including VAT`, the exclusions, and **no Serenity**.

---

## 9 · COMMIT AND PUSH

```bash
git add additional-home-universe-v1.json
git --no-pager diff --cached --stat
git commit -m "Regenerate the Additional Home universe from a fresh authoritative snapshot

Publishes BIOBUILDS Wanderlust under FX-BIOBUILDS-PUBLISH-20261011: EUR
105,000 Exterior Finished and EUR 163,000 Turnkey, both labelled, VAT
inclusive, 35.54 m2 verified internal area, Class 3A candidate, with the
three authorised supplier images, credit and link back.

Serenity is authorised and publishable but remains outside the 32-45 m2
Class 3A band with no usable area recorded, so it reaches no public surface.
No area was invented and the band was not widened.

verify-biobuilds-publication.mjs 20/20."
git log --oneline -1
git push origin main
```

If the push is rejected, **do not force it**. Run `git fetch origin`, read
`git log --oneline HEAD..origin/main`, and bring the two together with a merge
or rebase you have looked at.

---

## 10 · VERIFY THE LIVE SITE

Give the host a minute, then check the data first — it is the one thing that
can be verified mechanically.

```bash
curl -s https://plotnua.ie/additional-home-universe-v1.json \
| python3 -c '
import json,sys
d=json.load(sys.stdin)
g=lambda c:[x for x in d["products"] if x["productCode"]==c][0]
p,s=g("PROD-000523"),g("PROD-000524")
print("generated        ", d["generated"])
print("gate             ", d["publicationGate"]["version"])
print("Wanderlust       ", p["publicVisibility"], p["class3a"]["state"],
      p["area"]["number"], p["area"]["measurementBasis"])
print("  prices         ", " / ".join(c["label"]+" "+format(int(c["amount"]),",")
      for c in p["price"]["configurations"]), p["price"]["basis"])
im=p.get("imagery") or {}
print("  images         ", len(p.get("imagerySet") or []), "|",
      im.get("caption"), "|", im.get("credit"), "|", im.get("linkBack"))
print("Serenity         ", s["publicVisibility"], s["class3a"]["state"],
      s["class3a"]["reason"])
'
```

Run against the regeneration fixture, that prints:

```
generated         2026-10-11T15:48:03Z
gate              supplier-publication-gate-v1
Wanderlust        PUBLISHABLE CANDIDATE 35.54 VERIFIED_INTERNAL
  prices          Exterior Finished 105,000 / Turnkey 163,000 INCLUDES_VAT
  images          3 | BIOBUILDS model imagery | © BIOBUILDS | https://www.biobuilds.com/
Serenity          PUBLISHABLE NOT_A_CANDIDATE no-usable-area
```

Expect `generated` to be today, Wanderlust `PUBLISHABLE CANDIDATE 35.54
VERIFIED_INTERNAL`, both labelled prices, `INCLUDES_VAT`, 3 images,
`BIOBUILDS model imagery`, `© BIOBUILDS`, and Serenity
`PUBLISHABLE NOT_A_CANDIDATE no-usable-area`.

The images are served from the supplier's own domain, so confirm they resolve:

```bash
curl -s -o /dev/null -w "%{http_code}  %{url_effective}\n" -L \
  https://www.biobuilds.com/_next/static/immutable/media/wanderlust-catalog.3-furbv0o-vtc.jpg
```

### The public Results experience — a human check, by hand

**Deployment is not complete until this is done.** No script can stand in for
it: the harness in step 8 is localhost-only, and the live page reaches
Wanderlust only through the real journey.

1. Open **https://plotnua.ie/your-plot.html?discovery=residential**
2. Enter a real Eircode and complete the property journey.
3. On Results, confirm:
   - Wanderlust appears, with its three images
   - caption **BIOBUILDS model imagery**, credit **© BIOBUILDS**
   - the supplier link opens biobuilds.com
   - **€105,000 (Exterior Finished)** and **€163,000 (Turnkey)**, both named
   - *including VAT*, and the exclusions visible
   - nothing calls the imagery a photograph, a render or a visualisation
   - **Serenity does not appear**
4. Open Compare with Wanderlust selected: both configurations labelled, no
   ranking between them, **no imagery** — unchanged for this release by your
   decision.
5. Reload once. The card should be identical: nothing here depends on
   client-side state.

Check it on a phone as well as a desktop. If anything above is wrong, the
artefact is already live — say so immediately rather than adjusting it
quietly, and the fastest honest revert is to restore the previous
`additional-home-universe-v1.json` from git and push that.
