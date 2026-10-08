# POWERSHEDS SUPPLIER CORRECTION + POPULATION · FREEZE RECORD

**Status:** **CLOSED — PUSHED, DEPLOYED AND VERIFIED IN PRODUCTION** · 8 October 2026
**Release commit:** `a3a1b80` · pushed as a normal fast-forward,
`0969ece..a3a1b80 main -> main`. `refs/heads/main` at GitHub read back as
`a3a1b8024004bede88db6f01ec12374411497d3a` by `git ls-remote`, matching local
HEAD, with no working-tree delta on any of the ten corrected paths — so the
bytes verified and the bytes deployed are the same bytes.

| | |
|---|---|
| POWERSHEDS NAME CORRECTION | **CLOSED** |
| POWERSHEDS IMAGE RIGHTS | **ACTIVE** |
| POWERSHEDS SUPPLIER POPULATION | **VERIFIED** |

---

## 1 · AUTHORITY

Email from **Jack Sutcliffe, Powersheds**, received 8 October 2026, verbatim:

> Hello / Seems ok to me - can you just change Power Sheds to Powersheds? /
> Cheers / Jack Sutcliffe

**Two separate things are recorded, and they must not be conflated.**

**1. APPROVAL.** "Seems ok to me" is the supplier's approval of the PlotNua
supplier preview and the feature **as shown to him**.

**2. NAME CORRECTION.** An explicit correction of his own company's name.

### The approval is NOT an image-rights grant

This is the distinction that governs everything below. The approval widens
nothing. **`IPO-POWERSHEDS-0001` (`reczCyWXPWvoA27GX`), "Granted with
Conditions — Founder Confirmed", 28 September 2026, remains the sole governing
grant**, and its scope is unchanged: selected imagery from the Powersheds
website, used when featuring Powersheds on PlotNua, carrying the required
credit, exercised on one noindex unlisted page. Nothing in the 8 October email
was treated as permission for anything the 28 September grant did not already
cover.

### Canonical name

**Powersheds** — one word — is the canonical supplier-facing and
homeowner-facing name.

Corroboration already held first-party before the email: the registered entity
is **Powersheds Limited, UK company number 11790351**, and the 13 linked Source
records were already titled "Powersheds — …". The closed form is the company's
own name; "Power Sheds" was PlotNua's rendering of it.

### Founder decisions, 8 October 2026

- **Q1 = OPTION 1.** The governed credit becomes `Image: Powersheds`. Credit,
  grant record, manifest, preview and universe move **together**. Original
  permission evidence preserved verbatim; the dated correction appended.
- **Q2 = OPTION 1.** Canonical Airtable Organisation Name updated, dated note
  added. **Do not** rename the 158 internal Asset titles. **Do not** alter the
  40 product names. **No unnecessary Airtable writes.**

---

## 2 · HOW IT WAS APPLIED

One bounded builder: `atlas-tools/build-powersheds-name-correction.py`, ten
guards, every one demonstrated capable of failing. The builder is
idempotence-guarded and now correctly **refuses to re-run** against the
corrected files.

**Two guards fired on the first run. Both were re-specified, not relaxed —
because in both cases the guard was right and the specification was wrong.**

**G6 — operative fields only.** It fired on the preserved ORG-ID note, which
quotes `'Image: Power Sheds'` as the wording in force at the time. A guard that
refuses preserved history is a guard that would force the history to be
rewritten. Re-specified to test the **operative** fields — `required_credit`,
`conditions`, and all non-note row content — and to **deliberately permit**
`note` and `evidence` to quote the old name:

```python
row = dict(r); row.pop("note", None); row.pop("evidence", None)
if OLD in json.dumps(row, ensure_ascii=False):
    die("%s: %r survives OUTSIDE the note/evidence fields…")
```

**G8 — decision versus prose.** It fired on `qualification.reasons[2]`,
"Supplier attribution is confirmed: Power Sheds." Re-specified to separate the
two kinds of field: `DECISION_KEYS` must be **byte-identical**, while `reasons`
is prose and is rename-normalised, with the count of affected products asserted
exactly:

```python
DECISION_KEYS = ("status","confidenceTier","priceEvidence",
                 "caveats","hardBlockers","evidenceSignals")
if len(prose) != 3: die(...)
```

---

## 3 · WHAT CHANGED — TEN FILES, ONE COMMIT

| path | role |
|---|---|
| `atlas-recognition-pool.json` | **40 records** |
| `garden-room-recommendation-universe-v1.json` | **18 occurrences** |
| `garden-room-detail-suppliers-v1.json` | **2 occurrences** |
| `image-rights-records.json` | governed credit + grant record |
| `image-rights-manifest.json` | generated manifest |
| `powersheds-preview.html` | the preview page |
| `.github/scripts/apply_authorised_imagery.py` | imagery applier |
| `atlas-tools/prove-imagery-render.mjs` | guard assertion |
| `atlas-tools/prove-powersheds-grant.mjs` | guard display prose |
| `atlas-tools/build-powersheds-name-correction.py` | the builder (new) |

### Airtable — two writes only

`appoLZFWesvoPhZGR` / `tblngwmviAcWxFKsW` / **`recZyvRt8pDg5spUU`**:

1. `fldHZ4o52tJgE4dM8` Organisation Name: `Power Sheds` → **`Powersheds`**
2. `fldCjOzhsUYUnOQsf` note: dated correction section appended

Read back after the correction: Organisation Name = **Powersheds**, and the note
records the approval and the name correction **separately**, quotes Jack's email
verbatim, states that the grant is unchanged, and lists the deliberate
non-changes. **No other Airtable write was made.**

### Imagery activated

**Five authorised images**, all from
`cdn.shopify.com/s/files/1/0601/8967/1489/` — the supplier's own Shopify store
namespace, the store id being part of the prefix so the scope is their files and
nobody else's. Governed credit: **`Image: Powersheds`**.

---

## 4 · DELIBERATE NON-CHANGES

These are not omissions. Each one is a decision, and each one is load-bearing.

**Historical evidence preserved verbatim.** The `IPO-POWERSHEDS-0001` evidence
sentence still reads "Granted by Jack Sutcliffe of **Power Sheds** BY EMAIL,
Gmail thread 1a0b5d1a7cf5e664…", and the earlier ORG-ID-correction note is
preserved as written. Verified on the **live** manifest: all four surviving
occurrences of the old name sit inside `note` (3) and `evidence` (1), and
**zero** sit in any operative field. The dated correction is appended beneath
the original, never over it. Historical governance and commercial records that
say "Power Sheds" were left alone for the same reason —
`09 Commercial/POWER-SHEDS-*.md` is untouched and still records the name as it
stood.

**158 internal Asset titles not renamed.** Read back from Airtable after the
correction and confirmed unrenamed: "Power Sheds Apex Summerhouse —
Manufacturer Hero Photo", "Power Sheds 12x6 Premium Apex Potting Shed —
Lifestyle", and so on throughout. These are internal Atlas labels and are not
homeowner-visible.

**40 product names not renamed.** None contains the supplier name, so renaming
them would have been tidiness at the cost of unnecessary writes.

**No email sent or drafted to Jack.** No outbound reply is authorised. If a
reply becomes useful, the exact proposed text returns to the founder first.

**No switch changed.** `WRITES_ENABLED` = false. `EMAIL_ENABLED` = false.
`INTEREST_PUBLIC` = false. **G5 not executed.** No G4, no G7, no outreach, no
acquisition traffic.

---

## 5 · PRODUCTION VERIFICATION — 8 October 2026

Fetched live from `https://plotnua.ie`, cache-bypassed. Not localhost, not the
repository copy.

### Homeowner-facing operative surfaces

| file | HTTP | "Power Sheds" | "Powersheds" |
|---|---|---|---|
| `atlas-recognition-pool.json` | 200 | **0** | 40 |
| `garden-room-recommendation-universe-v1.json` | 200 | **0** | 18 |
| `garden-room-detail-suppliers-v1.json` | 200 | **0** | 2 |
| `powersheds-preview.html` | 200 | **0** | 33 |
| `image-rights-manifest.json` | 200 | 4 (note + evidence only) | 15 |

**No operative homeowner-facing "Power Sheds" remains anywhere in production.**

### Image-rights gate

**37 publishable · 0 refused · 0 not for publication · GATE PASS.** Identical
to baseline. All five Powersheds images **ALLOW**, each reporting *live grant,
rights agree, domain matches, required credit present*.

### Universe invariants — 573 products

Record count 573 before and after. Beyond counting: **the entire 4.1 MB
recommendation universe is identical once `Power Sheds` → `Powersheds` is
normalised.** Nothing else in it moved at all.

| invariant | result |
|---|---|
| `status`, `confidenceTier`, `priceEvidence`, `caveats`, `hardBlockers`, `evidenceSignals` | **0 changed** |
| price fields (`priceFrom`, `priceTo`, `price`, `budgetBand`) | **0 changed** |
| ranking fields (`rank`, `score`) | **0 changed** |
| `qualification.reasons` | **exactly 3** |

The three: 12x12 Apex Classic Log Cabin, 14x14 Apex Classic Log Cabin, 16x12
Apex Log Cabin.

### Live preview — https://plotnua.ie/powersheds-preview.html

- Title *PlotNua — a short introduction for Powersheds*; all 33 occurrences read
  Powersheds
- Both credit lines render as **`Image: Powersheds`** — the attribution caption
  and the removal-undertaking line
- All five images load, **0 broken**: 2500×2500, 1496×1496, 1859×1859,
  1846×1846, 2525×2525

### Responsive verification

| width | `scrollWidth` | horizontal page scroll | elements overflowing viewport |
|---|---|---|---|
| 1440 × 900 | 1440 | **none** | **0** |
| 375 × 812 (mobile UA, reloaded) | 375 | **none** | **0** |

No layout regression at either width.

### Private state preserved

`<meta name="robots" content="noindex, nofollow, noarchive, nosnippet,
noimageindex">`. **0** mentions in `sitemap.xml`. Unlinked from every other
page.

### Scope of the push

Eleven files across two commits, each attributable, nothing unrelated:

- `0ed8d2f` — `governance/PRE-G5-CORRECTION-FREEZE-RECORD.md` only
- `a3a1b80` — the ten Powersheds paths

---

## 6 · A FALSE POSITIVE FOUND DURING VERIFICATION — INSTRUMENT, NOT PRODUCT

**Recorded because the same mistake will recur, and it was one step from
becoming a reported defect.**

The first live image read returned all five images as `naturalWidth: 0`, which
reads exactly like five broken images. It was the instrument.

The browser pane was **hidden**, so the viewport measured **0×0**. Every image
on the page is `loading="lazy"` and sits **3,129px or more** down the document.
With no viewport there is no intersection, so no image had any reason to fetch.
Nothing was broken; nothing had been asked for.

With a real viewport emulated, all five load at full resolution and the broken
count is 0, as recorded in §5.

**The rule this establishes:** a lazy-loaded page read from a hidden pane
reports zero-size images whether or not they are sound. Image liveness must be
measured with a viewport, or by forcing the fetch, never by reading
`naturalWidth` out of a hidden pane. A measurement taken through a broken
instrument is not evidence, and had this been reported as a production fault it
would have sent a correct page back for repair.

---

## 7 · P12_no_new_css — PRE-EXISTING, OUT OF SCOPE

The certified supplier-preview QA returns **66 passed, 1 failed**, and the
guards return **12 passed, 1 failed per supplier**. The single failure is
`P12_no_new_css`, and it is **not** attributable to this correction:

- it fails **identically at the previous HEAD** for **all seven** previews,
  including suppliers this correction never touched
- the Powersheds page's inline stylesheet is **byte-identical** to the previous
  HEAD's
- cause: the provider-led template has grown to 837 lines against the pages'
  587 (`PREVIEW-GEOMETRY-001` and others landed after these pages were built)

**Recorded as a pre-existing stale cross-build guard and OUT OF SCOPE for the
Powersheds correction. Not repaired. Not suppressed. Not touched.** Widening
the blast radius of a bounded correction to silence an unrelated guard is the
thing bounded corrections exist to prevent. It is a real item for its own
bounded pass, and it stays open.

---

## 8 · GATE STATE AT CLOSE

| | |
|---|---|
| POWERSHEDS NAME CORRECTION | **CLOSED** |
| POWERSHEDS IMAGE RIGHTS | **ACTIVE** |
| POWERSHEDS SUPPLIER POPULATION | **VERIFIED** |
| Powersheds homeowner-visible in production | **YES**, under the correct name |
| `IPO-POWERSHEDS-0001` | **unchanged — the sole governing grant** |
| `WRITES_ENABLED` / `EMAIL_ENABLED` / `INTEREST_PUBLIC` | **false / false / false** |
| G5 | **not executed** |
| Email to Jack Sutcliffe | **none sent, none drafted, none authorised** |
| `P12_no_new_css` | **pre-existing, out of scope, open** |
