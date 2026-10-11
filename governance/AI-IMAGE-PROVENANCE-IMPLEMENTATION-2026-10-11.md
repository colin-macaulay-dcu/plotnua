# AI IMAGE PROVENANCE — IMPLEMENTATION RECORD

Founder policy approved and implemented 11 October 2026.
**No visible website imagery changed. No page caption changed.**

---

## 1 · THE RECOVERY, AND WHAT IT HONESTLY FOUND

The instruction was to search before declaring anything unknown. Five sources
were searched, by `atlas-tools/recover-image-provenance.py`, which is kept so
the search is repeatable rather than taken on trust.

| searched | found |
|---|---|
| Embedded metadata on every deployed asset | **0 of 101** carry any. All stripped. |
| Every path ever added or deleted, all git branches, for generation scripts, prompts, source manifests | **none have ever existed** |
| The master image library outside the repo (132 masters) | **77 deployed assets matched** to a named master |
| Embedded metadata on those matched masters | **0** show a camera or a tool |
| The git commit that introduced each asset | **recoverable for all**: a date and a release |

### The result, stated plainly

**Provenance CONTEXT was recovered for 77 of 101 assets.** For each: which
picture it is, which Discovery it served, which commit and date introduced it.

**Provenance CLASSIFICATION was recovered for ZERO.** Not one published image
carries evidence of what made it. So not one is declared.

That is not a failure of the search. It is the finding. Declaring 85 garden
scenes as `AI_ILLUSTRATION` because they look generated is precisely the
inference item 4 forbids — and it is also the inference that would make this
register worthless, because a register of guesses cannot be relied on later.

### Two findings worth the founder's attention

**Nine masters ARE photographs.** `DISC-022 Hidden Cars/IMG_8039–8054.jpeg`
and four DISC-002 files carry iOS `Software` tags and Apple MPF blocks. They
were taken on a phone. **Not one of them is among the assets that shipped** —
they stayed in the library — so nothing is published on that basis and nothing
is blocked.

**They do, however, expose a gap in the approved taxonomy.** A photograph taken
by PlotNua is neither a supplier's image nor an AI illustration. The three
approved states have nowhere to put a first-party photograph. The register
records this as an open question rather than resolving it: inventing a fourth
class was not authorised, and mis-filing a photograph as either of the other
two would be false. The first such image to be published will need one founder
decision. Recorded in the register under
`recovery.a_fourth_class_may_be_needed`.

### Two instrument errors I made and corrected

- The first metadata scan counted **every** key in `Image.info` and reported
  82 of 85 assets as carrying metadata. It was counting JFIF density and DPI.
  That would have overstated the recovery badly. The key set is now
  enumerated; the true figure is 0.
- The first inventory covered `assets/img` only. The provenance guard
  immediately caught three brand SVGs on published pages that were in neither
  the records nor the backlog — a hole in the ratchet. The inventory is now the
  whole of `assets/`, which is why the count is **101, not 85**.

---

## 2 · THE REGISTER

`image-provenance-records.json` — **a separate file**, as instructed.

Four reasons it is not a field on `image-rights-records.json`: AI illustrations
stay out of supplier permission records; that file's `source_of_record` is
Atlas Image Permission Outreach and an AI illustration has none; the two files
answer different questions (*may we publish someone else's image* versus *what
is this image*); and the rights manifest is generated and byte-compared in CI
behind an eleven-sabotage proof, so widening its schema is a large change to
carry a fact that does not belong in it.

```
records              0
legacy_undeclared    101   (77 carrying recovered master context)
```

A `SUPPLIER_IMAGE` row carries `rights_ref` — a **pointer** to the authorising
organisation row — and duplicates no permission data. The register grants
nothing, and P11 asserts that at source.

`NO_IMAGE` is recorded as **the state of a slot, not a class of asset**, with
the reason written down: if "no image" is not a respectable answer, the
pressure is always to fill the slot with something, and that pressure is how
laundering starts.

---

## 3 · THE GUARD · P1–P11

`atlas-tools/validate-image-provenance.js` — **11 checks, 11 passing.**

It closes the blind spot at `validate-image-rights.js:395`:

```js
if (!/^https?:\/\//i.test(u)) continue;   // relative = PlotNua's own
```

Sound when written. It means the rights gate examines 40 external supplier
images and skips 101 local ones, so a laundered supplier photograph saved into
`assets/` would pass it silently.

| | assertion | result |
|---|---|---|
| **P1** | every local image on a published page is declared or enumerated — **the ratchet** | 60 checked |
| **P2** | every record's SHA-256 matches the bytes on disk | 101 hashed |
| **P3** | the class vocabulary is closed, and `NO_IMAGE` is not in it | pass |
| **P4** | a `SUPPLIER_IMAGE` resolves to a live grant in the rights manifest | live, nothing to test yet |
| **P5** | an `AI_ILLUSTRATION` carries tool, date, prompt, explicit `reference_inputs`, named review | live, nothing to test yet |
| **P6** | no prompt or reference input names a supplier, organisation or product | 26 names and domains checked |
| **P7** | `product-card` is **not an available surface** | 6 surfaces |
| **P8** | a declared AI illustration carries its approved label | live, nothing to test yet |
| **P9** | no declared record describes an unreferenced asset | pass |
| **P10** | no AI illustration shares a caption or card with a supplier's name | live, nothing to test yet |
| **P11** | *(source)* a provenance record can never grant a permission | pass |

Checks that currently have nothing to assert **say so in their own output**
rather than printing a bare PASS. That is the condition in which a guard
quietly rots, so the capability proof drives all of them against synthetic
records instead.

### What P6 buys, and what it does not

It cannot look at two pictures and judge resemblance. **No check here can.**
What it does is make *intent* reviewable: a prompt naming a supplier is
refused, and `reference_inputs` turns "did you feed it their photograph?" from
an unanswerable question into a recorded assertion a named person signed. The
resemblance judgement stays human. P5 requires the attestation to exist; it
cannot require it to be true. The register says so.

---

## 4 · CAPABILITY PROOFS

**`prove-image-provenance-capability.mjs` — 20 mutations, 20 proved capable.**

Every check driven against a synthetic register holding the records that do not
exist yet. Includes both refusal cases: a missing register and an unparseable
one must **exit 2**, not pass.

**`prove-image-rights-gate-capability.mjs` — 5 mutations, 5 proved capable.** New.

---

## 5 · THE CI DEFECT

`.github/workflows/image-rights-gate.yml`, step *"Prove the image-rights gate
still catches what it is for"*:

```yaml
test -f atlas-tools/prove-image-rights-gate-capability.mjs \
  && node atlas-tools/prove-image-rights-gate-capability.mjs \
  || echo "no image-rights capability proof in this repo yet; see FOLLOW-UPS"
```

`prove-image-rights-gate-capability.mjs` **did not exist.** When the file is
absent, `test -f` fails, the `&&` is skipped, the `||` runs, `echo` returns 0
and the step is green. A required check that could never refuse anything.

**This was the second time.** The comment directly above it records the first
— the step pointed at a path in another repository and ended in the same
`|| echo`. It was "fixed" by re-pointing it at a filename that also did not
exist, and **keeping the `|| echo`**. Same defect, same step, introduced twice.

### The correction

```yaml
- name: Prove the image-rights gate still catches what it is for
  run: node atlas-tools/prove-image-rights-gate-capability.mjs
```

No `test -f`, no `||`, no fallback. A missing file now fails the build.

**And the proof now exists and is not a duplicate.** Running
`validate-image-rights.js --self-test` shows it already covers the six
scenarios the step's comment claims — unknown vocabulary, missing permission,
wrong domain, a live grant, withdrawal, rights disagreement, scoped delivery
hosts. So the missing file was not missing *that* coverage.

It was missing coverage of **the path CI actually runs**. `--self-test` feeds
the gate a synthetic asset list; production runs `--scan-html .`, which walks
the published pages. That is the path which catches a page that *gains* a
supplier image while the manifest is untouched — the case this workflow runs on
every publish to catch — and nothing proved it could refuse at all. It now
does, five ways:

| | mutation | result |
|---|---|---|
| C-SCAN1 | a page gains an image from an ungranted domain | REFUSED |
| C-SCAN2 | the granted supplier's image served from another domain | REFUSED |
| C-SCAN3 | the grant downgraded while the page is unchanged | REFUSED |
| C-SCAN4 | a conditional grant's required credit disappears | REFUSED |
| C-SCAN5 | the manifest emptied | REFUSED |

Control first: a page carrying a **granted** image passes the scan.

### The remaining `|| echo`, and why it stays

One remains, in the `Summary` step under `if: always()`:

```yaml
cat "${RUNNER_TEMP}/gate.txt" 2>/dev/null || echo "the gate did not produce output"
```

That is a fallback for `cat` when printing a log to the run summary. It is not
a substitute for a test and it gates nothing. Removing it would make a
cosmetic step fail when a log file is absent. Reported rather than "fixed".

### Three new required steps, none with a fallback

```yaml
- run: node atlas-tools/prove-image-rights-gate-capability.mjs
- run: node atlas-tools/validate-image-provenance.js
- run: node atlas-tools/prove-image-provenance-capability.mjs
```

`validate-image-provenance.js` exits 2 when it cannot establish the facts, and
exit 2 fails the build exactly as exit 1 does.

---

## 6 · LABELS — PREPARED, NOT APPLIED

Held in the register, applied nowhere:

| state | label |
|---|---|
| Confirmed AI imagery | `AI-generated illustration` |
| Other verified illustrations | `Illustration` |
| Unknown provenance | **none** |

An undeclared asset gets **no label**. Inventing a classification to fill a
caption is the error this register exists to prevent. **No published caption
changed**, and none will until the matching record exists.

---

## 7 · THE RATCHET

Every one of the 101 assets is enumerated by path and SHA-256. The guard
refuses any local image on a published page that is in neither `records` nor
`legacy_undeclared`, so **no new undeclared image can be added**. The count
prints on every run and in the CI step summary, and only ever goes down.

A legacy entry is **not** a declaration, **not** verified, **not** authorised
supplier imagery, and may not reach a product card or a supplier context.

Backfilling is now clerical: 77 entries carry their master file and Discovery,
so declaring them is a matter of recalling the tool and prompt per batch, not
archaeology. Where provenance genuinely cannot be recovered, the honest
outcomes are to re-generate with a recorded prompt, or to retire the image —
**not** to declare what nobody knows.

**A separate finding: 37 of the 101 are referenced by no published page.**
Probably from retired Discoveries. They stay in the backlog — the census is of
what is on disk — but they are candidates for retirement rather than
declaration.

---

## 8 · WHAT WAS NOT TOUCHED

- **Supplier permissions.** `image-rights-records.json` and its manifest are
  byte-unchanged. 13 rows, 12 live grants, 40 publishable assets, 0 refused.
- **The BIOBUILDS publication decision.** `FX-BIOBUILDS-PUBLISH-20261011`
  intact; 18/18 and 14/14 still pass.
- **Atlas pricing.** Untouched; 28/28 and 619 products unmoved.
- **Results and Compare.** Untouched; 19/19.
- **Existing publication gates.** Untouched; 14/14 and 14/14 capable.
- **Cluster 1.** Untouched; 18/18.
- **Every published page.** No HTML file was modified.
