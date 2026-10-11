# BIOBUILDS · IMAGERY PUBLICATION

Founder authorisation **FX-BIOBUILDS-PUBLISH-20261011**, extended
11 October 2026 to cover selected supplier imagery.

---

## 1 · THE SELECTION

Eight of the 34 governed BIOBUILDS assets are exercised on the private
preview. **Six are approved. Two are withheld.**

| product | asset | role |
|---|---|---|
| Wanderlust `PROD-000523` | `wanderlust-catalog` | exterior · **primary** |
| | `wanderlust-48-int-catalog` | interior |
| | `wanderlust-48-bedroom` | interior |
| Serenity `PROD-000524` | `serenity-catalog` | exterior · **primary** |
| | `serenity-95-int-catalog` | interior |
| | `serenity-95-bathroom` | interior |

**Withheld, by name:** `wall-section-3.0` (a construction detail of the wall
build-up) and `prefab-48-crane-lift` (a process shot of a module being
craned). Neither depicts a product a homeowner is choosing between. You
authorised *selected* imagery, and a selection that quietly included
everything would not be a selection.

The other 26 governed assets remain Reference Only.

**Approval is by enumeration.** An asset is publishable because it is written
down in `approved_assets`, never because it is served from biobuilds.com. The
manifest scopes by host and prefix and would pass any file on that host; the
enumeration is what makes the row narrower than the gate.

---

## 2 · GRANT CONDITION 7 — A CONSTRAINT I AM HONOURING

The rights record carries this, from the original grant:

> "THE MEDIUM OF THE MODEL IMAGERY IS NOT ESTABLISHED. BIOBUILDS has not said
> whether the model images on their site are photographs of completed homes or
> architectural visualisations, and the question has been put to them. Until
> they answer, no PlotNua surface may describe them as either."

Your instruction calls them photographs. **That is a description of intent,
not a constraint on wording, and the two do not conflict** — but it does mean
no caption or alt text may say *photograph*, *render* or *visualisation*.

The supplier's own caption is medium-neutral, which is exactly why it works:

> **BIOBUILDS model imagery**

Every published image carries that caption, `© BIOBUILDS`, a working link to
`https://www.biobuilds.com/`, and alt text that describes what is shown
without naming the medium and without claiming an Irish installation. Two
guards assert it: builder G5/G6 on the selection, and **BI8** on the emitted
payload.

**This is not a blocker.** Publication proceeds.

---

## 3 · RECORDS UPDATED

`image-rights-records.json` → `ORG-000153`, and the regenerated manifest.

```
asset_approval_state     REFERENCE_ONLY   ← the DEFAULT for unlisted assets
asset_approval.state     SELECTED_ASSETS_APPROVED
approved_assets          6     NEW
withheld_assets          2     NEW
pre_live_review_disposition    NEW
founder_exception.scope  WIDENED to cover the six enumerated assets
listing_review.state     AWAITING_CONFIRMATION   ← UNCHANGED
listing_review.confirmed_at  null                ← UNCHANGED
```

`pre_live_review_disposition` records three facts and tidies none of them
away: the supplier asked for a pre-live review, **has not answered**, and the
founder proceeded anyway. The earlier scoping note — that the grant "covers
the private preview only" — is recorded as superseded, with the reason: that
was PlotNua's own reading of its own restraint, not a limit BIOBUILDS placed
on the grant.

Mateus has still not confirmed the corrected preview, and nothing in this
change says he has.

---

## 4 · RESULTS — THE SMALLEST GOVERNED EXTENSION

**No display code was written.** A complete governed imagery layer already
exists in `your-plot.html`, built for the Garden Room pathway and used by six
of its 573 products:

```
pnImageRightsOk(im)     refuses an image missing url, credit, supplier,
                        rightsRecord or permittedPrefix; refuses any URL not
                        starting with that prefix; refuses anything not https
pnAuthorisedImage(p)    the primary, re-checked at render time
pnAuthorisedImages(p)   the authorised set, primary forced first
pnGovernedGallery       one gallery, shared by Results and Resolve
```

So the extension is two things: the generator emits an `imagery` block in the
shape that layer already reads, and `pnAdditionalHomeView()` passes it
through. Results hero, Results gallery cards, My Plot and Resolve then work
with no new rendering anywhere, and `pnImageRightsOk` / `pnAuthorisedImage` /
`pnAuthorisedImages` are **byte-identical** — builder G6 asserts that.

Three refusals are built into the generator's index:

- an asset not enumerated produces nothing;
- an approved asset whose `product_code` does not match produces nothing for
  that product;
- **a held product gets no imagery at all**, so the gate and the imagery
  cannot disagree about whether a supplier is public.

### NO_IMAGE

Unchanged and automatic. A product with no authorised asset passes
`undefined`, and every surface takes its existing no-image path. That is
every Additional Home product except these two, and 567 of 573 Garden Rooms.

---

## 5 · COMPARE — ONE SCOPED DECISION FOR YOU

Measured: **`renderCompare()` renders no imagery for any supplier.** Not for
BIOBUILDS, not for the six Garden Rooms that have authorised images, not for
anyone. The Compare matrix is text: price, VAT, exclusions, evidence.

So §6 and §5's "do not alter the existing Garden Room image architecture
unnecessarily" pull in opposite directions. Adding imagery to Compare is not
a BIOBUILDS change — it is a change to how Compare works for all 573
products.

**What I did:** nothing to Compare's imagery, and I am flagging it rather
than deciding it for you.

**What Compare already does correctly**, from commit `bdb7512`: both
configurations visible with their labels, VAT basis stated, exclusions
present, and `pnPriceDelta()` refusing to rank unlike configurations —
`€105,000 (Exterior Finished) · €163,000 (Turnkey) · including VAT`. Compare
cannot imply the two prices represent equivalent completed homes, because it
labels both and refuses the subtraction. 19/19 in
`prove-results-configurations.mjs`.

**If you want images in Compare**, it is a one-piece job affecting every
product and needs its own authorisation.

---

## 6 · SERENITY — AUTHORISED, PUBLISHABLE, AND IT WILL NOT APPEAR

| | |
|---|---|
| publication | **authorised**, `publicVisibility: PUBLISHABLE` |
| imagery | three assets **approved** |
| Class 3A | `NOT_A_CANDIDATE` · `no-usable-area` |
| if 95 m² were written | `NOT_A_CANDIDATE` · `outside-pathway-band` |

95 m² is genuinely outside the 32–45 m² auxiliary-dwelling route. I did not
write an area number and did not widen the band. **BI13** asserts both,
driving the real `_area_evidence()` and `class_3a()`.

You asked whether an existing public surface could display it. **Measured
answer: no.** `search-index-v1.json` carries 573 Garden Room products, 64
suppliers, 13 possibilities and 9 journeys — **no Additional Home product at
all**. The Class 3A Results pathway is the only public surface that lists
them, and Serenity cannot enter it truthfully.

Per your instruction I did **not** invent a pathway to display it. Its
approved imagery sits ready in the record and will publish the moment a
truthful surface exists.

**So this publication surfaces Wanderlust only**, with three images.

---

## 7 · PROOFS

| suite | result |
|---|---|
| `prove-biobuilds-imagery.mjs` | **14/14** — BI1–BI14, your ten requirements |
| `prove-biobuilds-imagery-capability.mjs` | **15 mutations, 15 proved capable**, tree hash-verified |
| `prove-biobuilds-containment.mjs` | **10/10**, re-aimed per asset |
| `prove-biobuilds-containment-capability.mjs` | **11/11** caught, tree hash-verified |
| `validate-image-rights.js` scan + self-test | 40 publishable, 0 refused · pass |
| `generate_image_rights_manifest.py --check` | manifest matches its records |
| `validate-image-provenance.js` | 11/11 · 101 local assets enumerated |
| publication gate · founder exception | 14/14 · 18/18, both capability proofs clean |
| pricing · configurations · Garden Room | 28/28 · 19/19 · 619 products unmoved |

### Containment, re-aimed rather than relaxed

C1 was "every BIOBUILDS image must be on the preview". It is now "every
BIOBUILDS image **outside** the preview must be one of the six enumerated
approved assets", plus C1b enforcing the withheld list. C2–C5 are untouched:
five robots directives, the credit twice over, the link back, no sitemap
entry, and the outcome still `Granted with Conditions` with the pre-live
review condition recorded.

**It is driven by data, not by this file.** Delete `approved_assets` and C1
immediately requires every BIOBUILDS image back on the preview alone — the
old behaviour, recovered by removing a record rather than editing a proof.

### A real blind spot found in C6

C6 scanned `atlas-*.json`. That pattern **never matched
`additional-home-universe-v1.json`** — the one payload that decides the
Additional Home Results pool, and the one that now carries the imagery. C6
had never looked at it. Widened, and it now checks three things per asset:
unapproved images, approved images on the wrong product, and any image on a
held product.

### Four of my own guards caught passing for the wrong reason

- **C1 / C6 capability mutations** copied an image that is now legitimately
  approved, so they planted something valid and the proof reported MISSED.
  Re-aimed at unapproved and withheld assets, with C1b and C6b added.
- **BI6 threw instead of failing** when a mutation emptied an index entry.
  A guard that cannot survive the defect it tests is not a guard. Made
  null-safe.
- **C-BI7 / C-BI7b** expected BI7 and got BI1/BI3 — because the generator
  refuses to index an asset missing its credit or alt text, so the system
  fails closed one layer *earlier* than my test assumed. Re-aimed at the layer
  that fires, and **C-BI7c** added to test BI7 directly.

---

## 8 · WHAT WAS NOT TOUCHED

Supplier permissions for the other 12 organisations · the Garden Room imagery
architecture (byte-identical predicates, 6 products still accepted) · Atlas
pricing · the publication gates · Cluster 1 · the provenance register · every
published HTML page except none — **no page was modified**.

No AI-generated image was created, used or substituted anywhere.
