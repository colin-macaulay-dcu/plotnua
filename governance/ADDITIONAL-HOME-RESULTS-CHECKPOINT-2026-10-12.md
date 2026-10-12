# ADDITIONAL HOME RESULTS — FOUNDER-ACCEPTED CHECKPOINT

**Status: ACCEPTED AS THE WORKING CHECKPOINT. LOCAL ONLY — NOT DEPLOYED.**
Founder acceptance, 12 October 2026. Development on this page is stopped here.

This record supersedes
`governance/ADDITIONAL-HOME-NO-LEAD-EQUALITY-2026-10-11.md`, which described an
architecture (`#ahCandidateSet` / `#ahCandidateGrid`) that was **retired before
implementation**. Nothing in that document describes the shipped page.

---

## 1 · WHAT THE PAGE NOW IS

The property's governed assessment is the main result, presented in the
**Garden Room Results components**, not in a parallel residential design.

Measured in the browser at 1280 (panel 910px), the two heroes are the same
object:

| | Garden Room | Additional Home |
|---|---|---|
| `h2.results-hero-name` | 66.56px | 66.56px |
| `.rh-split` | flex row, 26px gap | flex row, 26px gap |
| `.pn-media-col` | 582px | 582px |
| `.results-hero-media` | 582 × 437 | 582 × 437 |
| `.results-hero-body` | 302px | 302px |

**Page order** — hero, Atlas Assessment dossier, Atlas perspectives, building
options, property exploration, decision guidance, closing panel. The same
rhythm as Garden Room.

---

## 2 · THE GOVERNED POSITIONS THIS PAGE TAKES

**One verdict, one dossier.** The hero carries the headline, the locality and
pathway, one editorial sentence, and the planning boundary. Every figure,
confirmed finding and outstanding check lives **once**, in the dossier. The
hero no longer renders `results-hero-price-row` or `hero-trust` at all.

**No candidate is preferred.** Additional Home has no ranking:
`pnResidentialResults()` is a governed evidence filter in catalogue order, and
`pnCandidateSplit()` names a lead only when exactly one candidate is
caveat-free. On the current pool that is 0 of 4, so the page says *"None has
been established as a better match for your property."* All four plates are
identical geometry (599px at 1280).

**The hero image is illustrative, not a recommendation.** The BIOBUILDS
Wanderlust exterior is resolved through `pnAuthorisedImage()` — the governed
reader — from the candidate already in the result set. No URL is written into
the page; if the rights gate refuses the asset, no media column is appended and
the hero keeps the shipped `is-fieldonly` treatment.

Caption, verbatim:

> BIOBUILDS Wanderlust · Image courtesy of BIOBUILDS
> An example of an additional home in this range. Atlas has not placed it ahead
> of the other options.

**The medium is not claimed.** Grant `C2-GRANT-BIOBUILDS-20261002` records that
Atlas does not know whether BIOBUILDS' model imagery is photographic or a
visualisation, and forbids PlotNua describing it as either until they answer.
`build-ah-gr-template.py` refuses the build if `photograph`, `render` or
`visualisation` appears in any homeowner-visible string, and refuses equally on
`best` / `strongest` / `preferred` / `recommended` / `highest-ranked`.

**Grant conditions are rendered with the image.** `© BIOBUILDS` via the shipped
`pnAttachImageCredit()`; the required link back to `https://www.biobuilds.com/`
beside the caption.

**No invented trust.** No ratings, no review counts, no verification claims.
Only 2 of 61 organisations hold a verified Google Place ID (Modern Garden Rooms,
Garden Rooms) and neither appears on either journey, so no Google component
mounts. PlotNua stores no ratings at all by design — Google renders them
client-side.

---

## 3 · TWO PRE-EXISTING DEFECTS FOUND AND FIXED

**The planning disclaimer had never rendered.** `PN_VERDICT_BOUND` was declared
with `var` *after* the `COPY` object that references it. `var` hoists the
declaration but not the assignment, so all four verdict states received
`undefined` as their fourth part and the sentence *"not a planning decision, and
not a guarantee of eligibility"* appeared nowhere on the live page. The
declaration now precedes `COPY`; the text is byte-identical and the file length
is unchanged (a pure move).

**The Garden Room review harness could not render.** `enterResultsReviewMode()`
awaited `initCesium()` then `flyToLocation()` before `computeAndShowResults()`.
Google Photorealistic 3D Tiles answer **403 Forbidden** from a localhost origin,
that promise never settled, and the reference page sat on the entry screen —
making visual comparison impossible. The same four viewer functions now run in a
non-awaited chain with their own catch. **Review mode only**; production
behaviour, the Results design, the calculations, the product data and the image
rights are untouched.

---

## 4 · THE ONE OWNERSHIP RULE ADDED

`renderResultsDecide(null)` cleared "Before you decide" unconditionally, which
erased the Additional Home closing experience a moment after it was built. The
property result now marks the section `data-pn-residential-decide="1"` and the
no-product branch respects that marker. **Garden Room never sets it**, so its
behaviour is unchanged; `prove-lens-null-primary` R10/R10b assert both halves.

---

## 5 · VERIFICATION AT THIS CHECKPOINT

`node --check`: 0 inline scripts failing.

| suite | result |
|---|---|
| `prove-verdict-hero` | 43 / 43 |
| `prove-ah-results-parity` | 24 / 24 |
| `prove-no-lead-altresults` | 28 / 28 |
| `prove-lens-null-primary` | 12 / 12 |
| `prove-candidate-lead-honoured` | 16 / 16 |
| `prove-imagery-render` | PROOF COMPLETE |
| `prove-results-publication-gate` | PROOF COMPLETE |
| `prove-presentation-priority` | PROOF COMPLETE |

Every builder in this checkpoint carries guard-capability proofs: each guard was
shown to catch the fault it owns by mutating the applied build in a disposable
tree. Faults proved caught include an invented cost figure, the word
"approved", a claimed medium, a ranking word, a hardcoded supplier URL, an
unscoped CSS rule, a new component class, a dropped viewer call, a retained
`await`, and a change to Garden Room's product branch.

**Garden Room regression, both widths:** hero 651px at 1280 and 623px at 390,
its own photograph present, 3 cards, no residential marker, no caption leak, no
no-image-plate leak, `match-bring-your-own` not spanning, zero horizontal
overflow.

---

## 6 · HONEST LIMITS AT THIS CHECKPOINT

1. **Three of four buildings have no publishable image.** BIOBUILDS is the only
   organisation in `image-rights-records.json` with approved assets (10). The
   other three Additional Home suppliers hold no enumerated approvals and do not
   appear in the register. Their plates carry a composed no-image treatment
   reading "No image Atlas may publish". Only new permissions change this.

2. **The BIOBUILDS pre-live review is outstanding.** The supplier asked to see
   the listing before it goes live. Corrections were applied on 11 October 2026
   and their confirmation **has not been received**. Proceeding is covered by
   founder decision `FX-BIOBUILDS-PUBLISH-20261011`, which waives the wait and
   accepts the risk. If BIOBUILDS objects, remove the exception and the gate
   returns the product to HOLD.

3. **The 3D property hero was attempted and withdrawn.** It mounted but rendered
   black space with a Cesium watermark: `.rh-split` computed
   `flex-direction: column` and the camera never flew. Withdrawn under the
   founder's own condition — "provided it works reliably in the existing hero
   composition".

4. **Google 3D tiles 403 on localhost**, so Sun & Light and the 3D exploration
   show their fallback in review mode. An API-origin restriction, expected to
   behave normally on the live origin — unverified there.

5. **All four candidates carry the same governed reason sentence**, because
   Atlas holds nothing per-candidate that distinguishes them. A data limit, not
   a presentation one.

6. **Mobile card heights `[565, 565, 589, 565]`** — the 24px outlier is the
   longest product name wrapping. Desktop is exactly `[599 × 4]`.

---

## 7 · WHAT THIS CHECKPOINT DOES NOT INCLUDE

Deployment. This is a **local commit only**. Nothing has been pushed and the
live site is unchanged. Deployment is a separate founder authorisation.
