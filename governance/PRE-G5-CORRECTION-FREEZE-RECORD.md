# PRE-G5 CORRECTION · FREEZE RECORD

**Status:** **FULLY CLOSED — PUSHED, DEPLOYED AND VERIFIED IN PRODUCTION** · 8 October 2026
**Authority:** founder decisions D-G5-1 = **option 1 (FROZEN G1B §5 is
authoritative)**, D-G5-2 = option i, D-G5-3 = YES.
**Founder visual review of the buying state:** **PASS at 390px and 1440px.**

| | |
|---|---|
| PRE-G5 CONTRACT ALIGNMENT | **CLOSED** |
| PRE-G5 TEST-HARNESS CORRECTION | **CLOSED** |
| PRE-G5 PRODUCTION VERIFICATION | **PASS** |
| **PRE-G5 CORRECTION** | **FULLY CLOSED** |

Pushed as a normal fast-forward, `057bb81..0969ece main -> main`. Release HEAD
and `origin/main` both `0969ece`, confirmed by `git ls-remote`.

---

## 1 · WHAT CHANGED — FOUR LINES OF LOGIC

| site | before | after |
|---|---|---|
| Worker `handleGarden` | `if (tenure !== 'own')` | `if (tenure === 'rent')` |
| page `intPaintTenure()` | `tenure === 'rent' \|\| tenure === 'buying'` | `tenure === 'rent'` |
| page `intPayload()` | `answers.tenure && answers.tenure !== 'own'` | `answers.tenure === 'rent'` |
| page `intLocalProblem()` | same string as above | `answers.tenure === 'rent'` |

**The authoritative rule, as now implemented:**

| `inherited_tenure` | storable | permission_confirmed | garden_note | promotable |
|---|---|---|---|---|
| `own` | yes | not required | not required | — (G7) |
| `rent` | yes | **required** | **required, ≥20 chars** | — (G7) |
| `buying` | yes | **not required** | **not required** | **never** |
| absent / unconfirmed | **refused** — see §5 | — | — | **never** |

**G1B was NOT amended.** §5 keeps its exact frozen wording. Option 1 means the
contract was right and the implementation was stricter than it.

| artefact | before | after |
|---|---|---|
| `disc025-borrowed-garden-check.html` | `bd08ce67d004a8b24be00bc50e75a31bcf18693dd5e9dfb6974267917e327c19` | **`370bb493b742222206bc1f5a599796f4a6d34c17f8991793a694f49438da8195`** (+534 B) |
| `worker/garden-register/src/index.js` | `4c5a47831ec85178f083f4535f1bbb732ee9c4542af43f28ef8b88105897a3ba` | **`66ee90e2d94968ee59a1f2c71674956735b1f593c1d4ef7a97b77f477e177c79`** (+375 B, all comment) |
| `worker/garden-register/wrangler.toml` | `2a4b5c4cb8839deff581197839f296d0511b4a1e71a5e0cbe77d55ee4cb6ed30` | **byte-identical — no var touched** |

Switches, unchanged throughout: `INTEREST_PUBLIC = false` ·
`WRITES_ENABLED = "false"` · `EMAIL_ENABLED = "false"`.

**Deliberate non-change, recorded so nobody tidies it:** inside the now
rent-only block, `var who = (tenure === 'rent') ? … : 'the current owner'`
keeps its dead else arm. Collapsing it is not one of the approved changes.

---

## 2 · WHAT THE BUYING HOMEOWNER NOW MEETS

The owner's form. No permission tick, no "somebody else has to agree" hint, the
note box marked *Optional*. No new wording, no promise, nothing suggesting
`buying` is matchable or introducible. Verified in a real DOM across all three
harness states before the founder saw it, then approved at both widths.

No homeowner-visible field was added, removed or re-labelled, and no markup
changed: `#bgIntCond`, the checkbox, its label, the hint and the note field are
byte-identical. Only the JS that shows or hides them moved.

---

## 3 · THE FOUR COMMITS

| # | commit | paths |
|---|---|---|
| 1 | `aff7f78` builders + guard-capability provers | 4 under `atlas-tools/` |
| 2 | `d79d534` Worker tenure alignment | `worker/garden-register/src/index.js` |
| 3 | `d63039a` page tenure alignment | `disc025-borrowed-garden-check.html` |
| 4 | `e92d887` proof-suite corrections | 7 under `test/` + `build-g3-review-harness.py` |

**14 paths in total.** Explicit-path staging only — no `git add .`, no `-A`, no
`-a`, no amend. Confirmed absent from all four commits: `shadow-budget-v2`,
`tr4-inspect-candidate.py`, `outputs/` (derived captures, founder decision
D-D), `governance/`, `wrangler.toml`, `node_modules`. Both pre-existing stashes
untouched (2 before, 2 after). The nine unrelated untracked paths are still
untracked.

---

## 4 · PROOF AT FREEZE

**Page invariants, re-derived independently of the builder:**

| region | state |
|---|---|
| certified engine | **IDENTICAL** `72c0f466ab4aa198…` |
| `PlotNuaJourneySave` | **IDENTICAL** `df88b6e3bef36c4b…` |
| g3-html | **IDENTICAL** `829ff4f63724506c…` |
| g3-css | **IDENTICAL** `b7e873413ceb6dc7…` |
| g3-js | **CHANGED** `ef2cbbb44b1919f5…` → `ee9e30341b66ec65…` — the only region that moved |
| 240 engine outcomes | **240/240 identical**, `bc1cc28319275f53…`, including all 80 `buying` paths |

**Suites:**

| suite | result |
|---|---|
| `prove-g3.mjs` | **170 / 0** |
| `prove-guards.mjs` | **74 / 0** |
| `prove-g3-mutations.mjs` | **27 / 27 caught**, 0 blind |
| `prove-worker-mutations.mjs` | **3 / 3 caught**, 0 blind |
| **mutations, total** | **30 / 30 caught, 0 blind** |
| `prove-tenure-invariance.mjs` | **10 / 0** |
| `prove-g3-review-harness.mjs` | **46 / 0** on buying **and** own |
| `prove-g1b-tenure-builder-guards.py` | **15 / 15 capable**, 0 blind |
| `prove-worker-tenure-builder-guards.py` | **14 / 14 capable**, 0 blind |
| `node --check` | clean on the Worker and every test file |

**Payload invariance is the decisive one.** The `own` payload and the `rent`
payload are **byte-identical** before and after. `buying` drops **exactly one
key, `permission_confirmed`**, adds none, and changes no other value.

**Deployed Worker, writes off** — version
`352cc86d-3e37-4e25-bf26-bb512bf9e10c`, source `66ee90e2…`:

| probe | reply |
|---|---|
| `buying`, no tick, no note | **`503 not_open`** — was `400 refused · permission_confirmed` |
| `rent`, no tick | `400 refused · permission_confirmed` |
| `rent`, tick + short note | `400 refused · garden_note` |
| absent tenure | `400 refused · inherited_tenure` |
| `own` | `503 not_open` — unchanged |
| `buying`, bad district | `400 refused · district` |
| switch-independent suite | 11 / 0 |
| switch-dependent `--expect-closed` | 3 / 0 |

The last row of probes is the point: the `503` is the **write switch** talking,
not a validator that stopped working.

**Airtable, by direct read** — Gardens **0** · Growers **0** · Status log **0** ·
Consent proofs **0** · Incidents **0**. Each table queried individually with a
real field list. Not inferred from Worker replies.

---

## 5 · THE PRESERVED DIVERGENCE — NOT SOLVED HERE

FROZEN G1B §5 says absent/unconfirmed tenure is **storable, never promoted**.
The Worker **refuses** it:

```js
if (!tenure) return REFUSED(cors, 'inherited_tenure');
```

**Founder instruction, 8 October 2026: this is documented, not solved in this
correction.** It is unreachable through the homeowner journey, because
`decide()` only runs once every question is answered, so `inherited_tenure` is
always `own`/`rent`/`buying` when the register panel exists. It can only be
reached by a hand-written POST.

Three independent things now stop it disappearing quietly:

- Worker builder **guard 9** asserts the line is present before and survives after
- `prove-guards` **G35e, T9, T9b** assert the refusal still fires
- Worker mutation **M30** deletes the line and requires those three to fail —
  **caught**

---

## 6 · PUSH — OPEN, AND WHY

`git fetch` and `git push` over SSH **fail from this environment**:
`Host key verification failed`. There is no DNS for `github.com` over SSH,
`~/.ssh/known_hosts` is empty, and there are no identities. **An unverified host
key was not added.**

**The actual remote was still established, read-only over HTTPS**, rather than
trusting the stale local ref:

```
git ls-remote https://github.com/colin-macaulay-dcu/plotnua.git refs/heads/main
057bb814d4a0a46d30b821e867212a74b2797bd8  refs/heads/main
```

So `origin/main` is genuinely **unchanged at `057bb81`** — not merely unchanged
according to a local ref that a failed fetch left stale. Local `HEAD` is
`e92d887`, **4 ahead, 0 behind**, and `origin/main` **is an ancestor of HEAD**,
so the push is a clean fast-forward. No rebase, no force, no rewritten history.

**The push must run on the founder's Mac:**

```bash
cd "04 Deploy/plotnua-github"
git fetch origin
git log --oneline -1 origin/main        # must still be 057bb81
git rev-list --left-right --count origin/main...HEAD   # must be 0  4
git push origin main                    # fast-forward only; NO --force
```

If `origin/main` is anything but `057bb81`, **stop and inspect** before
integrating.

---

## 7 · PRODUCTION VERIFICATION — PASS

Verified against the **live site**, not localhost and not the repository copy,
in a real browser at origin `https://plotnua.ie`. The Worker probes were run
**from that origin**, which is what its exact-Origin CORS check requires.

| # | check | evidence |
|---|---|---|
| 1 | live file sha256 | **`370bb493b742222206bc1f5a599796f4a6d34c17f8991793a694f49438da8195`**, 141,272 bytes, HTTP 200, cache-busted — exact match |
| 2 | public switch | `var INTEREST_PUBLIC = false;` present; no `= true` anywhere. Both superseded conditions absent (0 occurrences); the three corrected ones present (1 + 2) |
| 3 | ordinary journey, no query string | result reached ("A corner of your garden looks workable"); **`#bgInterest` absent from the DOM, count 0**; not one of `bgIntOpen/bgIntForm/bgIntEmail/bgIntPerm/bgIntCond/bgIntNote` exists; Save to My Plot operational (`bgSave`, `bgSaveLink`, `PlotNuaJourneySave` live) |
| 4 | preview · **own** | permission block hidden (`offsetParent === null`), note hint `"Optional."`, no "somebody else has to agree" hint, `Private preview · not public` marker shown |
| 5 | preview · **rent** | permission block **shown**; label "I have asked your landlord or the owner…"; no tick → blocked, 0 requests, *"We still need the owner's permission."*; tick + 13-char note → blocked, 0 requests, *"We still need what you told us about the owner knowing."* |
| 6 | preview · **buying** | permission block hidden, note `"Optional."`, no hint, no label. **Real submission to the live Worker: HTTP 503 `{"ok":false,"state":"not_open"}`.** Payload carried `inherited_tenure: "buying"` with **`permission_confirmed` absent and `garden_note` absent**. Homeowner sees the approved closed state: *"The register isn't open yet"*, *"details haven't been saved"*, *"Property Check is unchanged"* |
| 7 | absent-tenure control | direct POST with `inherited_tenure` omitted → **`400 {"ok":false,"state":"refused","field":"inherited_tenure"}"`** — the preserved divergence holds in production |
| 8 | switches | page `INTEREST_PUBLIC=false`; Worker `WRITES_ENABLED="false"`, `EMAIL_ENABLED="false"`; version `352cc86d-3e37-4e25-bf26-bb512bf9e10c`. `--expect-open` was **not** run |
| 9 | Airtable, direct read | Gardens **0** · Growers **0** · Status log **0** · Consent proofs **0** · Incidents **0**. Five separate reads with real field lists, after the live submission |
| 10 | no unrelated change | the deployed diff touches 18 paths, of which **exactly one is site-visible**: `disc025-borrowed-garden-check.html`, +12/-4. Everything else is `atlas-tools/`, `governance/` or `worker/` — not published by Pages. `index.html`, `about.html`, `your-plot.html`, `sitemap.xml`, `robots.txt`, `_redirects`, `404.html`: **0 changed**. `wrangler.toml`: 0 |

**Positive controls alongside, from the live origin** — proving the `503` is the
write switch and not a validator that has stopped working:

```
own                        -> 503 {"ok":false,"state":"not_open"}
buying + bad district      -> 400 {"ok":false,"state":"refused","field":"district"}
rent, no tick              -> 400 {"ok":false,"state":"refused","field":"permission_confirmed"}
rent, tick + short note    -> 400 {"ok":false,"state":"refused","field":"garden_note"}
buying, no tick, no note   -> 503 {"ok":false,"state":"not_open"}
inherited_tenure omitted   -> 400 {"ok":false,"state":"refused","field":"inherited_tenure"}
```

Only four reply shapes exist: `{ok,state}` and `{ok,state,field}`. No reply
mentions a mail or token capability.

**One correction to my own instrument, recorded:** a first pass asserted that
no reply mentions `/mail|token|confirm|verify/` and reported a failure. The
regex was too broad — it matched the governed **field name**
`permission_confirmed`. Re-tested properly: the state replies mention no mail
or token capability, the refusal reply mentions none either, and
`permission_confirmed` is a contract vocabulary value, not a capability. My
assertion was wrong, not the product.

## 8 · G7 PREREQUISITE — GOVERNANCE, NOT CODE

**Recorded now. Do NOT implement it now.** G7 does not exist and is BLOCKED
pending the insurer / broker question (PS-3).

> **INTRODUCTION ELIGIBILITY MUST EXCLUDE:**
> - `buying`
> - absent tenure
> - unconfirmed tenure

This is where the obligation can actually be discharged. The correction makes
`buying` **storable**; it must never make it **introducible**. Nothing in the
Worker or the page promotes or introduces anybody today, and three guards
assert that stays true: Worker builder guards 12–13, page builder guard 14, and
`prove-guards` T10a–c (no introduction/promotion/eligibility logic; record
`status` only ever `SUBMIT_STATUS`; `'buying'` appears exactly once in
executable code, in the vocabulary).

---

## 9 · FAULTS FOUND DURING EXECUTION — ALL IN MY OWN INSTRUMENTS

Recorded because a guard that can lie in one direction can lie in the other.

| # | fault | resolution |
|---|---|---|
| 1 | Worker G15 secret sweep looked back only 200 characters for an opening `/*`, so it fired on the file's own 30-line header — **and its capability case passed for that wrong reason** | comment spans now computed over the whole file |
| 2 | My rewritten Worker comment dropped the comma after "lease" **and** wrapped the phrase across two lines. `prove-guards` **G36b caught it. The guard was right and I was wrong** | reverted, fixed at source, and added as builder guard G16 with its own capability case |
| 3 | The catch-all guard ran **first** in both builders, masking four working guards in each and reporting them blind | specific diagnosis now runs before generic, in both |
| 4 | The page builder's G11 normaliser had its own ordering bug — the short `tenure === 'rent'` rule ate the longer `answers.tenure === 'rent'`, so the guard fired on its own normalisation | order pinned by specificity, not site number |
| 5 | Two of three DENIALS used a typographic apostrophe where the source carries `&rsquo;`, so those assertions **could never have passed** and would have refused a correct patch | reduced to the one denial inside the region that may change; the other two are pinned byte-identical by guards 7 and 9 |
| 6 | G12 was mis-specified as set-equality, when losing `'buying'` and `'own'` from g3-js **is** the correction | now pins that nothing is added and exactly those two leave — a stronger claim |
| 7 | M28's expectation named G7, which tests `intPaintTenure` and is untouched by that mutation | expectation corrected to G10; product unchanged. Same class as the three over-broad expectations recorded during the G3 build |
| 8 | Four prover sabotages were mis-aimed (a retyped anchor, a `unicode_escape`-mangled one, one that matched `OLD` as well as `NEW`, and one that broke a widened anchor instead of the guard under test) | each re-aimed; anchors now imported from the builder rather than retyped |
| 9 | **A latent defect in `prove-guards`, not caused by this correction:** the Worker rate-limits POSTs at 30 per 60 s per isolate, keyed on the literal string `'post'` — global, not per-caller. The baseline sat just under; the added assertions pushed it over and three tail assertions returned 429, reading as three product defects | fresh module instance for those three. Fixed in the suite; the Worker was not touched |
| 10 | **`prove-deployed.mjs` claimed it "cannot create a record even if the Worker were wide open". That was false.** Both consent strings were byte-identical to the Worker's and both bodies valid, so D1/D2 were writes stopped only by the switch | split out to `prove-deployed-switch.mjs`, which refuses to run without an explicit mode; the header now says what was true |
| 11 | **Mutation M7 went stale** — its anchor was the condition this correction deleted, so it stopped applying | the harness reported it **VACUOUS, not passed**, which is why that distinction exists. Re-anchored |

Both capability provers read their pre-correction input **from git**, not from
disk, so they remain runnable now that the correction has landed. Read from
disk they would have been one-shot scripts.

---

## 10 · WHAT THIS DOES NOT AUTHORISE

- **`WRITES_ENABLED` stays `"false"`.** G5 is not executed and still requires
  separate founder authorisation.
- **`INTEREST_PUBLIC` stays `false`.** The buying state was reviewed through
  `?interest=preview`, which G5's plan already establishes needs no flip.
- **`EMAIL_ENABLED` stays `"false"`.** There is no mail adapter; flipping it
  would not enable email.
- **No Airtable record was created at any point**, including by the live
  buying submission made during production verification: five tables read
  directly afterwards, all 0. That is why rollback stays complete —
  `wrangler rollback` to `ed9d2dc6-69a0-4c88-91f3-9418a0954bc7`, or a revert
  commit on the page. No data exists to undo.
- **No G4. No G7. No outreach. No acquisition traffic.**
- **PS-1 CLOSED · PS-2 CLOSED · PS-3 OPEN**, scoped to G7 only.
- The G5 execution plan's case A4 is revised by this correction: `buying`
  becomes a straightforward accepted record with no permission evidence, and
  the expected-rows arithmetic returns to four Gardens rows.
