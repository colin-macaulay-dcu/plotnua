# G6 · GARDEN OWNER REGISTER — CONTROLLED ACTIVATION AND ROLLBACK RUNBOOK

**Written:** 12 October 2026
**Status:** PREPARED · NOT EXECUTED. Register CLOSED: `INTEREST_PUBLIC = false` · `WRITES_ENABLED = "false"` · nothing pushed · Worker not redeployed
**Authority:** founder authorisation "G6 release preparation authorised", 12 October 2026
**Related:** [`G6-PREPARATION-GARDEN-OWNER-REGISTER-2026-10-12.md`](G6-PREPARATION-GARDEN-OWNER-REGISTER-2026-10-12.md) · [`G6-R3-WORKER-DEPRECATED-FIELDS-2026-10-12.md`](G6-R3-WORKER-DEPRECATED-FIELDS-2026-10-12.md) · [`PRIVACY-VERSION-2026-10-PHASE2-V3.md`](PRIVACY-VERSION-2026-10-PHASE2-V3.md) · [`G3-TO-G6-DECISION-BRIEF.md`](G3-TO-G6-DECISION-BRIEF.md)

> **Every phase from B onward needs an explicit founder GO, given in that turn.**
> Nothing here is to be run on the strength of this document alone.

---

## 0 · Approval gates

| phase | what it does | founder GO needed | reversible by |
|---|---|---|---|
| A | build and test the release locally | **given 12 Oct** (preparation) | deleting local branches |
| B | push the release to GitHub `main` — panel still closed | **yes** | §7 RB4 |
| C | deploy the updated Worker — writes still off | **yes** | §7 RB3 |
| D | temporary writes-on controlled test, own records only, writes off again at the end | **yes** | §7 RB1 |
| E | open: writes on, then the opening commit published | **yes**, separately from D | §7 RB1 + RB2 |

---

## 1 · Release inventory (measured 12 October 2026)

| | |
|---|---|
| GitHub `main` | **`c64e63a`** — "Atlas statistics — refresh homepage figures", by `plotnua-atlas-bot`, 13:44 UTC. Touches `index.html` and `atlas-stats.json` |
| Founder's local `main` | `f8ab53a` — **1 behind, 14 ahead** of GitHub. A plain `git push` would be rejected, and must not be forced |
| Scheduled bot | `.github/workflows/atlas-stats.yml` pushes to `main` daily at **06:00 UTC**. Never overwrite its commits. Do not push near 06:00 UTC |
| Repository visibility | **PUBLIC.** Any branch pushed is world-readable. The release contains no credentials (checked) |
| Remote URL | `git@github.com:colin-macaulay-dcu/plotnua.git` (SSH). Push from the founder's Mac |

The 14 local-only commits on `main`:

| group | commits | released here? |
|---|---|---|
| Wellness / Garden Retreat (incl. Irish Sauna Company audit, W2, W3) | `b765fbf` `dd512dd` `b6cf9e1` `5df4964` `8c69caa` `af9b7d3` `6025164` `e43f237` `0d60e4c` `9cbee25` `cf6c089` | **NO** — unfinished; would publish `wellness-journey-private.html` and change the image-rights records |
| Proof scratch cleanup | `9a0c517` | **NO** — test tooling, not needed by this release |
| Borrowed Garden G6 | `9287489` `f8ab53a` | **YES**, as cherry-picks |

### The release branch

`release/g6-register`, checked out at `04 Deploy/plotnua-g6-release` (a git worktree of the same repository, so the founder's `plotnua-github` folder stays on `main`, untouched):

```
<runbook commit>  G6 release: controlled activation runbook (this file)
e7e0636           G6 release prep A: pin two proofs to a public baseline
94da418           G6 R3: the Worker refuses deprecated Property Check fields   (cherry-pick of f8ab53a)
a9facb3           G6 prep: Garden Owner Register ...                         (cherry-pick of 9287489)
c64e63a           GitHub main (bot commit) — base
```

**Public pages that change:** `disc025-borrowed-garden-check.html` and `privacy.html` — nothing else on the site. No Wellness / Garden Retreat file is present on the branch (`wellness-journey-private.html`, `wellness-universe-v1.json` and `generate_wellness_universe.py` are absent).

### The opening branch — NOT part of the release

`opening/g6-register` = the release branch **plus one commit**, "G6 opening (PREPARED, NOT RELEASED)". It flips `var INTEREST_PUBLIC = false;` to `true` through `atlas-tools/build-g6-open-register.py` and inverts the guards that assert "closed". It is **not merged** into the release and must not be pushed before Phase E.

---

## 2 · Test requirements (run before B, and again before E)

From `04 Deploy/plotnua-g6-release` on the branch being released. Dependencies, once per checkout:
`(cd worker/garden-register && npm ci)` and `npm i --no-save --no-package-lock jsdom@30.1.2`.

| command | expected on `release/g6-register` | expected on `opening/g6-register` |
|---|---|---|
| `node worker/garden-register/test/prove-g3.mjs` | 196 / 196 | 197 / 197 |
| `MUT_SLICE=0:12`, `12:24`, `24:` `node worker/garden-register/test/prove-g3-mutations.mjs` | 36 caught in total | 36 caught in total |
| `node worker/garden-register/test/prove-g6-deprecated-fields.mjs` | 72 / 72 | 72 / 72 |
| `node worker/garden-register/test/prove-g6-worker-mutations.mjs` | 10 caught | 10 caught |
| `node worker/garden-register/test/prove-guards.mjs` | 74 / 74 | 74 / 74 |
| `node worker/garden-register/test/prove-worker-mutations.mjs` | 3 caught | 3 caught |
| `node worker/garden-register/test/prove-tenure-invariance.mjs` | 12 / 12 | 12 / 12 |
| `python3 atlas-tools/prove-g6-owner-register.py` | 43 / 43 | 43 / 43 |
| `python3 atlas-tools/prove-g6-worker-builder.py` | 10 / 10 | 10 / 10 |
| `python3 atlas-tools/prove-g6-open-register.py` | (file not present) | 14 / 14 |
| `node atlas-tools/prove-landmarks.mjs` | 140 / 140 (L13 "remains false") | 140 / 140 (L13 "is true") |
| `python3 atlas-tools/prove-landmarks-capability.py` | 18 / 18 | 18 / 18 |
| `python3 atlas-tools/prove-journey-exit-mutations.py` | 19 caught | 19 caught |
| `python3 .github/scripts/generate_image_rights_manifest.py --check` then `node atlas-tools/validate-image-rights.js --scan-html . --permissions image-rights-manifest.json --max-age-days 30` | up to date · GATE PASS, 40 publishable | same |

**Known failures that are NOT caused by this release.** Each also fails on a clean checkout of GitHub `main`:

| proof | why it fails |
|---|---|
| `prove-disc026-discovery.mjs` | long-standing |
| `prove-founder-exception.mjs` and `-capability.mjs` | need an untracked `atlas-tools/publication-gate.mjs.bak` that exists only in the founder's working folder |
| `prove-supplier-publication-gate*.mjs` | write to a hard-coded `/tmp` path |

**Commit A was verified in a clone that holds only the release history.** `9a0c517` and `9287489` are absent from that clone. Before A, `prove-g6-worker-builder.py` crashed there. After A, both re-pinned proofs pass.

---

## 3 · Privacy checks (before B)

| check | state |
|---|---|
| Airtable DPA signed | **founder confirmed, 12 Oct** |
| Only the founder has human access to base `appUie3wPmPITfMW7` | **founder confirmed, 12 Oct** |
| Airtable "Share to web" off | **founder confirmed, 12 Oct** |
| All five register tables empty | **measured 12 Oct**: Gardens 0 · Growers 0 · Status log 0 · Consent proofs 0 · Incidents 0 |
| `privacy_version` fields accept V3 | **yes** — single-line text in Gardens, Growers and Consent proofs; no schema change needed |
| privacy.html Section 7, the inline notice V3 and the consent sentence (SHA-256 `85c43608…`) | on the release branch, guarded by PV1–PV16 and G23 |
| Worker refuses the four deprecated keys | in source (`17bdc467…`); **not yet deployed** |
| Legal review of Section 7 | recommended, founder decision |
| hello@plotnua.ie monitored for leaving / deletion requests | founder to confirm who reads it; respond within one month |

---

## 4 · Phase B — publish the release, register still CLOSED  *(founder GO required)*

```bash
cd ~/"Documents/PlotNua/04 Deploy/plotnua-g6-release"
git fetch origin
git log --oneline -1 origin/main          # expect c64e63a; if not, see B-retry
git status                                # expect: clean, on release/g6-register
git push origin release/g6-register:main  # a fast-forward; NEVER --force
```

**B-retry** — if the push is rejected because the bot has pushed since:

```bash
git rebase origin/main
```

Re-run §2, then push again. The bot only changes `index.html` and `atlas-stats.json`, so no conflict is expected.

**Verify after GitHub Pages has published** (usually a few minutes):

```bash
for f in disc025-borrowed-garden-check.html privacy.html; do
  echo "$f  live=$(curl -s https://plotnua.ie/$f | shasum -a 256 | cut -c1-16)  branch=$(shasum -a 256 $f | cut -c1-16)"
done
curl -s https://plotnua.ie/disc025-borrowed-garden-check.html | grep -c "var INTEREST_PUBLIC = false;"   # expect 1
curl -s -o /dev/null -w "%{http_code}\n" https://plotnua.ie/wellness-journey-private.html                # expect 404
```

Then check in a browser:
- the plain URL shows **no** register panel
- `?interest=preview` shows the new wording with "Private preview · not public"
- privacy.html shows Section 7
- the **image-rights-gate** workflow run for this push is green on GitHub Actions

**Reconcile the founder's local `main` afterwards** — rehearsed on a throwaway clone, see §8.

---

## 5 · Phase C — deploy the updated Worker, writes still OFF  *(founder GO required)*

From `04 Deploy/plotnua-g6-release/worker/garden-register`, with `wrangler.toml` unmodified:

```bash
grep -E '^(WRITES|EMAIL)_ENABLED|^PRIVACY_VERSION' wrangler.toml
#   WRITES_ENABLED  = "false"   EMAIL_ENABLED = "false"   PRIVACY_VERSION = "2026-10-PHASE2-V3"
npx wrangler whoami
npx wrangler deployments list        # RECORD the current version id = ROLLBACK_ID
npx wrangler secret list             # expect AIRTABLE_TOKEN and AIRTABLE_BASE
npx wrangler deploy                  # RECORD the new version id
```

### C-verify-1 — the deprecated-field refusal is live

Create two request bodies once, outside the repository:

```bash
cat > /tmp/g6-valid.json <<'JSON'
{"first_name":"Runbook","email":"runbook-check@plotnua.ie","district":"raheny","water":"outside_tap","size_note":"small","timing":"flexible","inherited_tenure":"own","over_18":true,"consent_text":"I'm over 18, and I'd like PlotNua to keep this and tell me if someone nearby is looking for growing space.","source":"direct"}
JSON
python3 -c "import json;d=json.load(open('/tmp/g6-valid.json'));d['inherited_result_key']='ARRANGEMENT';json.dump(d,open('/tmp/g6-deprecated.json','w'))"
```

Then define the helper (the same headers a browser sends from plotnua.ie):

```bash
W=https://plotnua-garden-register.colin-a41.workers.dev/v1/garden-register/garden
post() { curl -s -w "  HTTP %{http_code}\n" -X POST "$W" -H "Origin: https://plotnua.ie" \
  -H "Sec-Fetch-Site: cross-site" -H "Sec-Fetch-Mode: cors" -H "Content-Type: application/json" --data @"$1"; }
```

| command | expected | meaning |
|---|---|---|
| `post /tmp/g6-deprecated.json` | `{"ok":false,"state":"refused","field":"inherited_result_key"}  HTTP 400` | the new Worker is live. **A `503 not_open` here means the OLD code is still deployed** |
| `post /tmp/g6-valid.json` | `{"ok":false,"state":"not_open"}  HTTP 503` | the switch is off |

### C-verify-2 — the deployed negative controls

```bash
node test/prove-deployed.mjs
node test/prove-deployed-switch.mjs
node test/prove-g3-deployed.mjs
```

All three should report a closed register.

Confirm all five Airtable tables are still at **0**.

---

## 6 · Phase D — one controlled registration  *(founder GO required; writes OFF again at the end)*

The register panel stays closed to the public throughout (`INTEREST_PUBLIC = false`). Only the founder, using `?interest=preview`, can submit.

1. **Zero check.** Confirm all five tables are at 0.
2. **Writes on (temporary):**
   ```bash
   sed -i '' 's/^WRITES_ENABLED  = "false"/WRITES_ENABLED  = "true"/' wrangler.toml
   npx wrangler deploy
   ```
   Do **not** commit this edit.
3. **Refused requests write nothing, even with writes on.**
   - `post /tmp/g6-deprecated.json` → expect `400 refused inherited_result_key`.
   - Airtable is still 0 in all five tables.
4. **One registration through the real page:**
   - Open `https://plotnua.ie/disc025-borrowed-garden-check.html?interest=preview`.
   - Answer the Property Check as an **owner** with a garden.
   - Choose **I'm interested in offering garden space**.
   - Use your own address, e.g. `colin+g6test@…`, district Raheny.
   - Tick consent and join. Expect **"You're on the register"**.
5. **Verify in Airtable.** Gardens should have one record with:
   - `inherited_tenure` = own
   - **no** `inherited_spare_corner`, `inherited_way_in`, `inherited_your_own_use`, `inherited_result_key` or `check_saved_at`
   - `status` = `interest_submitted`
   - `privacy_version` = `2026-10-PHASE2-V3`
   - `consent_text_hash` starting `85c43608`
   - `source` = `garden_interest`

   Status log should have one row: Gardens · system · `submission_accepted`, from `""` to `interest_submitted`.

   Consent proofs should have one row: a 64-character `email_hash`, V3, `consent_text_hash`, `given_at`. **No email address.**
6. **Repeat check.** Submit the same address again → "You're on the register", and **no** new rows anywhere.
7. **Deletion test**, as for a real leaving request (PRIVACY-V2 §7):
   - (a) delete the Gardens record;
   - (b) delete the Status log rows matching **both** its `record_ref` and `table = Gardens`;
   - (c) stamp `erased_at` on the matching Consent proof;
   - (d) confirm the Consent proof **survives** and holds no address.
8. **Writes off — immediately, before anything else:**
   ```bash
   git checkout -- wrangler.toml && grep '^WRITES_ENABLED' wrangler.toml   # "false"
   npx wrangler deploy
   post /tmp/g6-valid.json        # expect 503 not_open
   ```
9. **Clean-up of test data.** The surviving Consent proof is the founder's own test record. As in G5, delete it to return to **0 / 0 / 0 / 0 / 0**, and record that it was deleted, and why, in the D record. `consent_id` is an autonumber and continues from where it is; that is expected.
10. Write the D record: version ids, timings, each verification above, and the final zero counts.

**Stop condition:** if anything in steps 3–7 does not match, go straight to step 8, then §7. Do not proceed to E.

---

## 7 · Rollback

Fastest first. Each step is independent.

| | action | effect | when |
|---|---|---|---|
| **RB1 · stop writes** | in the worktree: `git checkout -- worker/garden-register/wrangler.toml` (or set `WRITES_ENABLED = "false"`), then `npx wrangler deploy` | seconds. Any submission gets the honest "The register isn't open yet… haven't been saved" | **always first** |
| **RB2 · close the panel** | on `main`: `git revert <opening commit>`, then `git push origin main` | the panel is removed from the DOM again once GitHub Pages republishes | after RB1, if E has happened |
| **RB3 · Worker code** | `npx wrangler rollback <ROLLBACK_ID>` | restores the previous Worker. **Only with writes off**: the old code accepts the deprecated fields | only if the new Worker misbehaves |
| **RB4 · release revert** | on `main`: `git revert` the release commits, then push | page and privacy.html back to the V2 state | **only while closed and with zero records**, because it removes privacy Section 7 |
| **RB5 · data** | records made under the V3 notice are kept and honoured, not silently deleted. Log anything unexpected in **Incidents**. Answer leaving requests as normal | | |

**Triggers:** any record carrying a deprecated field · a record without its consent proof · repeated "That didn't go through" (Airtable `unavailable`) · a spam surge · a wording or privacy error · anything that implies matching is live.

Never use `git push --force` on `main` — it would destroy the bot's commits.

---

## 8 · Phase E — open the register  *(separate founder GO; only after D passed)*

1. **Re-test.** Run §2 on `opening/g6-register`. If GitHub `main` has moved, rebase the opening branch onto `origin/main` first.
2. **Writes on, permanently:**
   - In `04 Deploy/plotnua-g6-release`: `git switch opening/g6-register`.
   - Set `WRITES_ENABLED = "true"` in `wrangler.toml`.
   - Commit it as "G6 opening: writes enabled", so the repository matches production.
   - `npx wrangler deploy`.
   - `post /tmp/g6-deprecated.json` → 400. Airtable still 0.
3. **Publish the opening:** `git push origin opening/g6-register:main` (fast-forward; never force).
4. **Verify live on the plain URL** (no `?interest=preview`):
   - the panel shows **without** the preview ribbon;
   - a "no garden" answer shows **no** panel;
   - mobile is fine;
   - submit one record of your own;
   - verify it in Airtable exactly as in D-5;
   - delete it exactly as in D-7;
   - clean up as in D-9, back to zero.
5. **Start the weekly review** (§9). Record the opening time.

### After B, and again after E — reconcile the founder's local `main`

```bash
cd ~/"Documents/PlotNua/04 Deploy/plotnua-github"
# The release adds governance/G3-TO-G6-DECISION-BRIEF.md, which exists here
# UNTRACKED with identical content; git refuses to overwrite it, so move it
# aside first (compare, then remove the spare copy).
mv governance/G3-TO-G6-DECISION-BRIEF.md /tmp/G3-TO-G6-DECISION-BRIEF.local.md
git fetch origin
git rebase origin/main     # replays the 12 Wellness/Garden Retreat/tooling commits;
                           # the two G6 commits are dropped as already upstream
git log --oneline origin/main..main | wc -l   # expect 12
```

This was rehearsed on a throwaway clone (the rebase result is recorded in the G6 release report). It leaves the Garden Retreat work unpublished and local.

---

## 9 · Pilot governance

**A genuine garden-owner registration** (founder definition, 12 October 2026):
- a unique, non-test submission
- an adult registrant
- ownership, or stated permission to offer the garden space
- usable contact details
- genuine interest in participating

Registration does **not** mean the garden has been verified, inspected or approved.

How each test is applied at weekly review, using only what the register holds:

| criterion | evidence in the record | note |
|---|---|---|
| unique | one record per `email_key`; the Worker already refuses to write a repeat | |
| non-test | not a founder test address and not junk | |
| adult | `over_18 = true` | the registrant's own statement |
| ownership or stated permission | `inherited_tenure = own`; or `rent` with `permission_confirmed = true` and a statement | **`buying` needs a founder ruling.** It is storable under G1B §5 but is neither ownership nor stated permission, so it is **not counted** until decided |
| usable contact | a plausible, well-formed address | not verifiable without contacting the person. PlotNua does not email registrants except to answer them or under the notice's own terms |
| genuine interest | nothing in the note suggests otherwise | |

**Target:** five genuine registrations, **or eight weeks from opening, whichever comes first** — then stop and evaluate. This is a research count. It is never a promise of matching or introductions to anyone on the register.

**Weekly review:** the procedure in [`G6-PREPARATION-…` §6](G6-PREPARATION-GARDEN-OWNER-REGISTER-2026-10-12.md), applying the definition above. Do not change `status`, do not stamp `human_review_by` / `human_review_at` (reserved for G7), and do not contact registrants except to answer them.
