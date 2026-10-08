# PRE-G5 · STEP 4 HANDOVER — THE DEPLOYED WORKER PROOF

**Status:** steps 1–3 and Change B COMPLETE locally. Step 4 requires commands I
cannot run. 8 October 2026.

**Why this is handed over.** The sandbox has no outbound network except npm and
HTTPS git reads. `fetch` to `plotnua-garden-register.colin-a41.workers.dev`
returns `EAI_AGAIN`, and there are no `wrangler` credentials here. The deployed
proof exists precisely because *a deployment can carry different vars than the
file on disk*, so it cannot be simulated locally — the local in-process suite
already proves the source (74/0), and that is a different claim.

**Nothing is committed. Nothing is pushed. No switch has moved.**

| | |
|---|---|
| Worker source, corrected | `66ee90e2d94968ee59a1f2c71674956735b1f593c1d4ef7a97b77f477e177c79` (21,668 B) |
| Worker source, previous | `4c5a47831ec85178f083f4535f1bbb732ee9c4542af43f28ef8b88105897a3ba` (21,293 B) |
| `wrangler.toml` | `2a4b5c4cb8839deff581197839f296d0511b4a1e71a5e0cbe77d55ee4cb6ed30` — **byte-identical, no var changed** |
| page | `bd08ce67d004a8b24be00bc50e75a31bcf18693dd5e9dfb6974267917e327c19` — **untouched, step 5 not started** |
| switches | `WRITES_ENABLED="false"` · `EMAIL_ENABLED="false"` · `INTEREST_PUBLIC=false` |
| deployed version at freeze | `ed9d2dc6-69a0-4c88-91f3-9418a0954bc7` — record the new id beside it |

---

## 4.1 · DEPLOY THE WORKER, WRITES STILL OFF

```bash
cd "04 Deploy/plotnua-github/worker/garden-register"

# Confirm what is about to deploy, before deploying it.
shasum -a 256 src/index.js        # must be 66ee90e2d94968ee...
grep -nE '^(WRITES_ENABLED|EMAIL_ENABLED)' wrangler.toml   # both "false"

npx wrangler deploy
```

Record the new version id. **If `wrangler.toml` shows anything but `"false"`
for either var, STOP** — that is a listed stop condition.

---

## 4.2 · THE DECISIVE PROBE · buying with NO tick and NO note

This is the whole point of the correction. Before it, this returned
`400 refused · permission_confirmed`. It must now pass every validator and be
stopped only by the write switch.

```bash
BASE=https://plotnua-garden-register.colin-a41.workers.dev

curl -sS -i -X POST "$BASE/v1/garden-register/garden" \
  -H 'content-type: application/json' \
  -H 'origin: https://plotnua.ie' \
  -H 'sec-fetch-site: cross-site' \
  -H 'sec-fetch-mode: cors' \
  -d '{"first_name":"G5","email":"g5-buying@plotnua.invalid","district":"donnycarney","water":"outside_tap","size_note":"small","timing":"flexible","inherited_tenure":"buying","over_18":true,"consent_text":"I'"'"'m over 18, and I'"'"'d like PlotNua to keep this and tell me if someone nearby is looking for growing space."}'
```

**Required:** `HTTP/2 503` and body `{"ok":false,"state":"not_open"}`.

**Any of these is a STOP:**

- `400 ... "field":"permission_confirmed"` — the correction did not deploy
- `400 ... "field":"garden_note"` — likewise
- `400 ... "field":"consent_text"` — the consent sentence was mistyped in the
  curl above, so the 503 was never reachable; fix the quoting and retry. This
  one is a probe fault, not a product fault, and must not be read as a pass
  or a failure of the correction.
- `200 ... "received"` — **writes are ON.** Stop immediately and check Airtable.

---

## 4.3 · THE FOUR CONTROLS THAT MUST STILL HOLD

Same headers as above; only the body changes. Each must write nothing.

| # | body change | required reply |
|---|---|---|
| a | `"inherited_tenure":"rent"`, no `permission_confirmed` | `400 refused · permission_confirmed` |
| b | `"inherited_tenure":"rent","permission_confirmed":true,"garden_note":"ok"` | `400 refused · garden_note` |
| c | `"inherited_tenure"` omitted entirely | `400 refused · inherited_tenure` |
| d | `"inherited_tenure":"own"` (nothing else changed) | `503 not_open` — unchanged |
| e | `"inherited_tenure":"buying","district":"cork"` | `400 refused · district` |

**(e) is the positive control that matters.** It proves the 503 in 4.2 is the
switch talking and not a validator that has stopped working. **(c)** proves the
absent-tenure divergence is preserved, as instructed.

---

## 4.4 · THE SUITES

```bash
cd "04 Deploy/plotnua-github/worker/garden-register"
BASE=https://plotnua-garden-register.colin-a41.workers.dev

node test/prove-deployed.mjs "$BASE"                      # expect 12 passed, 0 failed
node test/prove-deployed-switch.mjs "$BASE" --expect-closed   # expect 3 passed, 0 failed
```

`prove-deployed.mjs` is now **switch-independent and safe with writes on**:
D1/D2 moved out and the false "cannot create a record" header is corrected
(D-G5-3). `prove-deployed-switch.mjs` refuses to run without an explicit mode,
and `--expect-open` prints the six rows it would write before writing them.
**Do not pass `--expect-open` during this correction.**

---

## 4.5 · AIRTABLE, IMMEDIATELY AFTERWARDS

All five tables must still read **0**, by direct read, not inference:

```
Gardens        tbltT83xG6E09PhjW
Growers        tblHECGCBXQDz6Kqc
Status log     tblB61wADVHxJB0b2
Consent proofs tblIuSP62HLWg4EYF
Incidents      tbl3HiqUivrsnGndl
```

Verified `0 / 0 / 0 / 0 / 0` at pre-flight today, before any work. No write
path has been exercised since: writes are off and this sandbox cannot reach
`api.airtable.com`.

**Any row at all is a STOP condition.**

---

## WHAT COMES BACK TO ME

Paste the reply bodies for 4.2 and 4.3(a–e), the two suite totals, the new
Worker version id, and the five Airtable counts. Step 5 — the bounded page
correction, its builder and its guard-capability proof — begins only after
that, and the page is not touched until then.

## ROLLBACK, IF 4.2 OR 4.3 FAILS

```bash
npx wrangler rollback            # to ed9d2dc6-69a0-4c88-91f3-9418a0954bc7
# or re-deploy the committed base:
cd "04 Deploy/plotnua-github"
git show 057bb81:worker/garden-register/src/index.js > /tmp/base.js
shasum -a 256 /tmp/base.js       # must be 4c5a47831ec85178...
```

Nothing is committed and nothing is pushed, so the local rollback is
`git checkout -- worker/garden-register/` and the three new untracked files.
**No Airtable record exists to roll back**, which is why this correction was
sequenced before `WRITES_ENABLED` is ever flipped.
