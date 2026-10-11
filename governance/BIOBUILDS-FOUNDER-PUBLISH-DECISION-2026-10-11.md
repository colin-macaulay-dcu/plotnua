# BIOBUILDS · FOUNDER DECISION TO PUBLISH

**Decision reference: `FX-BIOBUILDS-PUBLISH-20261011`**
Authorised by Colin MacAulay, Founder, 11 October 2026.

---

## 1 · WHAT WAS DECIDED, AND WHAT WAS NOT

**Decided:** BIOBUILDS' product listing is published in public Results,
Compare and search, without waiting for the supplier to confirm the corrected
preview. The founder accepts responsibility for proceeding before that
confirmation.

**Not decided, and explicitly out of scope:** publication of BIOBUILDS
imagery on any public page. The imagery grant remains scoped by this record's
own conditions to the private, noindexed review preview.

**Not claimed, anywhere:** that Mateus confirmed the corrected preview. He has
not. The record says so in two places and five guards refuse any file that
says otherwise.

---

## 2 · THE AUTHORISATION THIS RESTS ON

Mateus, BIOBUILDS, 2 October 2026, verbatim and preserved in the rights
record:

> "Yes. We are happy for PlotNua to feature BioBuilds and use selected images
> from our website, with credit and a link back to us. We supply the Republic
> of Ireland. Please send us the listing before it goes live, so we can check
> it."

Three separate things in one message: permission to **feature**, permission to
use **imagery** with conditions, and a request for a **pre-live check**. The
founder's decision exercises the first, leaves the second scoped as it was,
and proceeds without the third.

Recorded in Atlas as Image Permission Outreach `C2-GRANT-BIOBUILDS-20261002`
(`rec6JPwNYPIj7EIfZ`), Organisations `ORG-000153` (`recjNpnrIr2KT5BWh`),
outcome "Granted with Conditions — Founder Confirmed".

---

## 3 · HOW THE HOLD WAS REMOVED

There were three ways to make the gate let this through. Two were refused.

**Refused — set `listing_review.state` to `CONFIRMED`.** It would have been
one word. It would also have been a false statement about a named supplier,
in writing, in PlotNua's own records, and it would have outlived the decision
and misled everyone who read the file afterwards. The founder forbade it and
it would have been wrong regardless.

**Refused — relax the `AWAITING_CONFIRMATION` condition.** That is the global
weakening the founder forbade. It would silently publish the next supplier who
asks for a pre-live check.

**Taken — a documented, dated, named exception to specific conditions for one
supplier.** The condition is not removed and the review state is not altered.
The derivation still finds `listing-review-awaiting-confirmation`. It then
finds an exception that explicitly names that reason, and publishes anyway,
carrying the waiver in its own output so no surface can report a waived hold
as a satisfied condition.

What was written onto `ORG-000153`:

```
listing_review.state            AWAITING_CONFIRMATION   ← UNCHANGED
listing_review.confirmed_at     null                    ← UNCHANGED
asset_approval_state            REFERENCE_ONLY          ← UNCHANGED
permission                      GRANTED, 2026-10-02     ← UNCHANGED
evidence (Mateus's words)       verbatim                ← UNCHANGED
conditions (all 7)              intact                  ← UNCHANGED

founder_exception               NEW
  authorised_by                 Colin MacAulay
  decision_date                 2026-10-11
  decision_ref                  FX-BIOBUILDS-PUBLISH-20261011
  supplier_confirmation_received  false
  waives                        listing-review-awaiting-confirmation
                                assets-not-approved
public_visibility               HOLD → PUBLISHABLE
hold_reason                     listing-review-awaiting-confirmation → null
waived_conditions               NEW, both reasons listed
```

### The line that cannot move

`NEVER_WAIVABLE` holds `permission-declined`, `no-permission`,
`permission-conditional-unresolved` and `permission-state-missing`. **No
exception can waive any of them.** A founder may accept the risk of
publishing early against a grant PlotNua holds; a founder cannot conjure a
grant that was never given. Without that list this mechanism would be a
master key.

Measured during the capability proof: that line is held by **three**
independent layers, not two — the `NEVER_WAIVABLE` check, the
`WAIVABLE_HOLD_REASONS` allowlist, and a re-check inside the waiver loop.
Removing any one of them changes no behaviour. Only taking all three down
publishes an unpermitted supplier, and FX11 catches that.

---

## 4 · THE NEAR-MISS THAT NEARLY SHIPPED

The exception was built. The record was written. The JS derivation agreed.
Eighteen assertions passed and twenty mutations proved capable. Then driving
the **generator's own** gate function over the real records returned:

```
publication_hold('BIOBUILDS') -> 'listing-review-awaiting-confirmation'
```

The generator keeps its own copy of the rule — deliberately, so a held
supplier cannot be published even if the runtime reader is bypassed — and that
copy knew nothing about founder exceptions. **Regenerating on the founder's
Mac would have stamped `publicVisibility: HOLD` onto both products, the
runtime's second lock would have withheld them, and the authorised
publication would simply not have happened.** Every guard would have stayed
green, because every guard was pointed at the other two mirrors.

**THREE MIRRORS OF ONE RULE** is the standing hazard in this architecture:

| mirror | file |
|---|---|
| authoritative | `atlas-tools/publication-gate.mjs` |
| Python, for the record writer | `atlas-tools/build-publication-gate-records.py` |
| Python, inside the generator | `.github/scripts/generate_additional_home_universe.py` |

The third was the one nobody had taught. PG11 is re-aimed so the generator's
agreement is asserted from now on rather than assumed: it checks that the
generator frees BIOBUILDS **on the decision**, holds it again **without one**,
and shares the unwaivable list with the JS gate.

---

## 5 · WHAT PUBLICATION ACTUALLY SURFACES

Driven through the real `_area_evidence()` and `class_3a()` on the real
Airtable values:

| | area | basis | Class 3A | appears in Results |
|---|---|---|---|---|
| **Wanderlust** | 35.54 m² | VERIFIED_INTERNAL | **CANDIDATE** | **yes** |
| **Serenity** | no number held | UNRESOLVED | NOT_A_CANDIDATE · no-usable-area | no |

**Serenity will be publishable and will not appear.** Its Internal Floor Area
FeatureValue (`recfKKSgT8RqgwJlO`) carries the text "95 m² total floor area.
Per BIOBUILDS Homes catalog listing." and no `Value Number`. Even if 95 were
written as a number, `class_3a()` returns `outside-pathway-band`: 95 m² is
genuinely outside the 32–45 m² Class 3A auxiliary-dwelling route.

**No number was written for Serenity, deliberately.** The text says "total
floor area" — a catalogue figure with an unresolved measurement basis, which
the session record already flags as unverified. Writing 95 as a verified
number would manufacture certainty and would change nothing about publication.

So this decision publishes **one product in the Additional Home pathway**, and
that is the truthful outcome rather than a shortfall.

---

## 6 · PRICES AND VAT, VERIFIED AGAINST AIRTABLE

All four Pricing rows read from the live base on 11 October 2026. Every figure
matches the authorisation exactly; all four are Currency EUR, Status Verified,
`Price Includes VAT` = Yes.

| product | configuration | price | record |
|---|---|---|---|
| Wanderlust | Exterior Finished | €105,000 | `reccFXgzN2N6KepuW` |
| Wanderlust | Turnkey | €163,000 | `recnHZrHnYPG494XW` |
| Serenity | Exterior Finished | €191,000 | `recTQrnCzBN4irZ6E` |
| Serenity | Turnkey | €306,000 | `recrCqAw0NIPNxobb` |

**Finding — the 23% is prose, not a structured value.** There is **no
`VAT Rate %` field in the Pricing table**. `_vat_rate_of()` reads it and
therefore always returns `None`, so `vatRatePercent` is always null. The 23%
is evidenced only in each row's `Known Exclusions` text. Nothing
homeowner-facing depends on it — the reader prints "including VAT" with no
rate — so no correction was made and none is needed. Recorded so the next
person reading `vatRatePercent: null` does not treat it as missing data.

---

## 7 · IMAGERY: NOTHING IS PROPOSED FOR PUBLICATION

The founder asked that all BIOBUILDS images proposed for publication be
verified against the written permission. Measured:

- `pnAdditionalHomeView()` in `your-plot.html` carries **no imagery field at
  all**;
- the Additional Home generator **emits no image block**;
- the only BIOBUILDS images anywhere in the published tree are on
  `biobuilds-preview.html`, which carries
  `noindex, nofollow, noarchive, nosnippet, noimageindex`, appears in no
  sitemap, and is reachable only by the URL the supplier was sent.

**Zero BIOBUILDS images are proposed for publication**, so there is nothing to
approve and the 34 governed assets stay "Reference Only — Not Published" in
Atlas, truthfully. `prove-biobuilds-containment.mjs` continues to fail CI if a
biobuilds.com image appears anywhere other than that preview, or if the page
loses a robots directive. The image-rights gate passes with 40 publishable
assets, 0 refused.

That is also why `assets-not-approved` could be waived without widening
anything: the waiver's scope says in writing that it does not authorise
imagery, and the containment proof is what makes that scope real rather than
a sentence in a note.

---

## 8 · PROOFS

| suite | result |
|---|---|
| `prove-founder-exception.mjs` | **18/18** — FX1–FX17 |
| `prove-founder-exception-capability.mjs` | **20 mutations, 20 proved capable** |
| `prove-supplier-publication-gate.mjs` | **14/14** — PG3 and PG11 re-aimed |
| `prove-supplier-publication-gate-capability.mjs` | **14/14 caught**, real tree hash-verified untouched |
| `prove-biobuilds-containment.mjs` + capability | pass · 9/9 |
| `prove-preview-only-containment.mjs` | pass |
| `validate-image-rights.js` (gate, self-test, grant proof) | 40 publishable · 0 refused |
| `generate_image_rights_manifest.py --check` | manifest matches its records |
| `prove-price-configurations.py` | 28/28 |
| `prove-results-configurations.mjs` | 19/19 |
| `prove-price-presentation-unchanged.mjs` | 619 products, zero prices moved |
| `prove-landmarks.mjs` · `test_price_contract.py` | 140/140 · 64/64 |

### Guards re-aimed rather than relaxed

- **PG3** — "an outstanding review holds a supplier" now reads "unless a
  named founder decision explicitly accepts that exact condition". The
  synthetic probe, which carries no exception, must still derive HOLD. A
  record publishable with an outstanding review and *no* decision still fails.
- **PG11** — was "the generator holds BIOBUILDS", which was correct until the
  decision and is now wrong. Re-aimed to four assertions (§4).
- **C-PG1, C-PG2, C-PG6, C-PG11** — four capability mutations aimed at a
  baseline the decision legitimately changed, each reported BLIND by the proof
  and re-aimed.

### Four test-design errors the capability proof caught in my own guards

Reported here because a guard that passes for the wrong reason is worse than
no guard:

- **FX9** forged a record tripping *both* fabricated-confirmation branches, so
  removing either left it passing on the other. Split into FX9 and FX9b.
- **FX16** tested the derivation, which can never see an unrecognised hold
  reason. Re-pointed at the validator, where it bites.
- **FX11** was unreachable twice over before the three-layer finding (§3).
- **FX17** added as an explicit *source* assertion, labelled as such, because
  the third layer cannot be distinguished behaviourally.

---

## 9 · HOW TO UNDO THIS

Delete `founder_exception` from the BIOBUILDS record in
`image-rights-records.json`, re-run
`python3 atlas-tools/build-publication-gate-records.py`, regenerate the
manifest, and regenerate the universe. The gate returns the product to HOLD
with no other change, at all three mirrors. Nothing else has to be reverted,
and BIOBUILDS may request change or removal at any time exactly as the
original grant provides.

---

## 10 · WHAT WAS NOT WEAKENED

- **No other supplier.** 12 other records checked: none has an exception, none
  has a waived condition (FX14). An exception is per-record and names its
  reasons by hand.
- **The general gate.** All 157 no-exception cases — 144 synthetic across every
  state combination plus all 13 real records with any exception stripped —
  derive exactly what they derived before the mechanism existed (FX15).
- **The eight hold reasons.** Same names, same order, same vocabulary, at all
  three mirrors.
- **The area firewall.** PG6 still holds: six area values per record,
  including 35.54 inside the band, change `publicVisibility` not at all.
  Correcting a measurement still publishes nobody.
- **The Cluster 1 garden-room system.** Untouched; PG9 asserts the two Class 3A
  populations stay disjoint.
