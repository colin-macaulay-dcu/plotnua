# PLOTNUA — DEFAULT PRODUCT JOURNEY UI · DESIGN FREEZE

**Frozen:** 1 October 2026
**Scope:** the Results page and the Resolve page, as the default presentation
system for every eligible product in the universe.

---

## 1 · WHAT IS FROZEN

The approved Results and Resolve compositions are the **default**, not a
treatment that happens to suit one supplier. Concretely:

| Surface | Frozen element |
|---|---|
| Results | hero (media well + copy), runner-up cards, alternatives carousel |
| Resolve | editorial hero, YOUR PROPERTY answer panel, QUESTIONS TO SEND WITH YOUR ENQUIRY, closing strip |
| Both | the governed media well and the one gallery that serves it |

**These surfaces are not redesigned supplier by supplier.** A request to change
how one supplier's product looks is a request to change the default for all 477,
and is treated as such.

---

## 2 · THE DEFAULT IS GENERIC — MEASURED, NOT ASSERTED

`atlas-tools/prove-default-templates.js` runs the shipped decision code over the
whole universe on every invocation. Measured today:

- **477 products, 65 distinct organisations** — none crashes the imagery gate.
- **146 verified-price / 331 quote-only or unpriced** — both routes covered.
- **6 with governed imagery / 471 without** — both states covered.
- **5 YOUR PROPERTY rows for every product**; enquiry questions distribute
  14 × five, 170 × six, 293 × seven. **No product renders nothing.**
- **Zero supplier names in executable code** outside one frozen data table.

### The one permitted supplier-named thing

An adjudicated supplier→county lookup exists because Atlas holds no structured
`supplierCounty` field:

```
'My Garden Room (Barna Buildings)': ['Wicklow'],
'Granny Flats Dublin':             ['Kildare'],
'Kodasema': null, 'Koto': null, 'Iglucraft': null,
```

That is **data**, recorded and adjudicated. It is not a layout or styling fork.
The proof excludes it explicitly and then requires the rest of the file to be
clean. Yardbox and Power Sheds appear **zero** times in executable code.

---

## 3 · SUPPRESSION RULES (FAIL CLOSED)

Where evidence or rights are insufficient the default shows **less**, never a
guess:

| Missing | Behaviour |
|---|---|
| No live image grant | Results falls back to the branded placeholder; **Resolve paints nothing at all** — a continuation says a missing photograph better with silence than with a second placeholder |
| No verified price | `PB046_NO_PRICE` / `PB046_AMBIGUOUS_PRICE`; no figure is implied |
| Sparse Resolve evidence | fewer enquiry questions, never an invented one; five is the observed floor |
| No homeowner answer | the row asks, it does not assume |
| Enquiry transport | `ENQUIRY_ENABLED_ORGS` is frozen empty; the closing strip shows the deliberate pending state. **Still held.** |

---

## 4 · MEDIA — ONE IMAGE vs MANY

**The rule.** One governed authorised image → exactly the current single hero.
Two or more → the full authorised set as a gallery. The presence of more images
changes only the **media presentation**, never the Results or Resolve structure.

**How it is enforced.**

- `pnImageRightsOk(im)` — the per-image rule, declared **once**.
- `pnAuthorisedImages(product)` — the gated, deduplicated, primary-first set.
  Accepts `imagery` as a single object or `imagerySet` as an array.
- `pnAuthorisedImage(product)` — unchanged for all ten existing callers; now
  defined as the first member of the set. Verified identical for **477/477**.
- `pnGovernedGallery(mediaEl, images)` — declared **once**, called from exactly
  **two** sites (the Results hero and the Resolve hero), and **inert below two
  images**. Results and Resolve therefore cannot show different pictures.
- `pnPaintGoverned(imgEl, im, creditEl)` — the **only** place a governed image is
  painted from a set. The rights check, the assignment and the attribution are
  the same act, so an unauthorised or uncredited image cannot be drawn.

**A set is not a unit of permission.** Each image is gated individually: an
uncredited or prefix-drifted member is dropped and the rest still publish.
Withdrawing the rights record empties the set entirely.

**Where the gallery is deliberately NOT shown.** The alternatives-carousel cards
draw the primary image only. A thumbnail strip inside a 38%-wide runner-up card
is a worse card, not a richer one. **The rule is by surface, never by supplier.**

### The honest limit

**No product in the universe currently carries two governed images.** The
generator's curated asset list holds 7 entries across 12 products, none linked
to more than one. The gallery is therefore **correct but unexercised against
real data**, and its behaviour above one image is proven only against synthetic
sets — which the proof states in its own output rather than implying coverage it
does not have.

### The defect this pass fixed on the way

`apply_authorised_imagery.py` did `by_product[pid] = {...}` inside a loop over
assets. A second asset naming the same product **silently destroyed the first**,
with no guard firing. It is now an ordered, deduplicated list. Regenerating the
universe from the same base with the old and new generators produces a
**byte-identical** artefact, because `imagerySet` is written only at two or more.

---

## 5 · GOVERNANCE

| Gate | Status |
|---|---|
| `atlas-tools/validate-journey-contract.js` | **86 checks, held** |
| …its own capability proof | **22 / 22 mutations caught** |
| `atlas-tools/prove-default-templates.js` | **held**, 477 products, 65 orgs |
| `apply_authorised_imagery.py --prove` | **held**, incl. the new set guard |
| `prove-imagery-multi-guards.py` | **11 / 11** |
| `prove-governed-gallery-guards.py` | **13 / 13** |

J11 now verifies the painter **by shape** — its rights check must be the first
statement and it must make exactly one assignment — and applies its unchanged
variable-provenance rule to every other surface. That is one more obligation
than before, not one fewer. Widening J11 to trust the name `im` would have
reopened the hole its own comment warns about: *a name is not a permission.*

---

## 6 · WHAT THIS FREEZE DOES NOT CHANGE

`RESOLVE_REGISTRY` · evidence ownership and truth · product identity · image
rights · pricing semantics · the **enquiry live-send hold** · ranking · the
journey contract's visible path (RESULT → RESOLVE → ENQUIRY/HANDOFF) · the
**573 universe HOLD**.
